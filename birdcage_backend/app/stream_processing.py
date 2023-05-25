from flask import current_app
from celery import group, shared_task
from app.views.streams import get_streams_list
import time
from datetime import datetime
import os
from pathlib import Path
import ffmpeg
import uuid
from app.models.preferences import get_all_user_preferences
from app.models.detections import add_detection
from config import ANALYZE_SERVER, ANALYZE_PORT, TEMP_DIR_NAME, DETECTION_DIR_NAME
import json
import requests
from app.models.recording_metadata import set_metadata, get_metadata_by_filename, delete_metadata_by_filename
import glob
from pydub import AudioSegment
from .filter_functions import update_birdsoftheweek_table, create_birdsoftheweek_table, getaction
import subprocess

basedir = os.path.dirname(os.path.abspath(__file__))
DETECTION_DIR = os.path.join(basedir, '..', DETECTION_DIR_NAME)
TEMP_DIR = os.path.join(basedir, '..', TEMP_DIR_NAME)


@shared_task(name='update_birdsoftheweek_table_task')
def update_birdsoftheweek_table_task():
    update_birdsoftheweek_table()


def get_youtube_stream_url(youtube_video_url, format_code=None):
    youtube_dl_command = ["youtube-dl", "-g"]

    if format_code:
        youtube_dl_command.extend(["-f", str(format_code)])

    youtube_dl_command.append(youtube_video_url)

    stream_url = subprocess.check_output(youtube_dl_command).decode("utf-8").strip()
    return stream_url


def record_stream_ffmpeg(stream_url, protocol, transport, seconds, output_filename):
    try:
        if protocol == 'rtsp':
            (
                ffmpeg
                .input(stream_url, rtsp_transport=transport.lower())
                .output(output_filename, format='wav', t=seconds, loglevel='warning')
                .run()
            )

        elif protocol == 'youtube':
            youtube_stream_url = get_youtube_stream_url(stream_url, format_code=91)
            (
                ffmpeg  
                .input(youtube_stream_url)
                .output(output_filename, format='wav', t=seconds, loglevel='warning')  
                .run()
            )
        else:
            (
                ffmpeg
                .input(stream_url)
                .output(output_filename, format='wav', t=seconds, loglevel='warning')
                .run()
            )
        return {'status': 'success', 'filepath': output_filename}
    except ffmpeg.Error as e:
        print(f'Error: {e}')
        return {'status': 'failure', 'error': str(e)}


@shared_task
def record_stream(stream, preferences):

    app = current_app._get_current_object()
    celery = app.celery

    # Create the temp dir if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # Extract properties from the stream object
    stream_id = stream['id']
    name = stream['name']
    address = stream['address']
    protocol = stream['protocol']
    transport = stream['transport'] if 'transport' in stream else None
    seconds = preferences['recordinglength']

    while True:

        # Generate a unique temporary filename
        tmp_filename = TEMP_DIR + f'/{uuid.uuid4().hex}.wav'

        # Record the stream for 15 seconds and save it to the output file
        result = record_stream_ffmpeg(address, protocol, transport, seconds, tmp_filename)

        if result['status'] == 'success':
            # The recording was successful
            print(f"Recording successful. File saved to: {result['filepath']}", flush=True)
            set_metadata(os.path.basename(tmp_filename),
                         stream_id, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        else:
            # The recording failed
            print(f"Recording failed. Error: {result['error']}")

        # Sleep for some time before recording the stream again
        time.sleep(1)


def sendRequest(fpath, mdata):
    url = 'http://{}:{}/analyze'.format(ANALYZE_SERVER, ANALYZE_PORT)

    print('Requesting analysis for {}'.format(fpath), flush=True)

    # Make payload
    multipart_form_data = {
        'audio': (fpath.split(os.sep)[-1], open(fpath, 'rb')),
        'meta': (None, mdata)
    }

    try:
        # Send request
        response = requests.post(url, files=multipart_form_data)

        # Convert to dict
        data = json.loads(response.text)

        return data
    except Exception:
        return {'msg': 'fail'}


def check_results(results, filepath, recording_metadata, preferences):

    confidence_target = float(preferences['confidence'])
    # Load the wav file
    wav_audio = AudioSegment.from_wav(filepath)

    for time_interval in results:
        interval_results = results[time_interval]

        # Split the time_interval string into start and end times
        start_time, end_time = map(float, time_interval.split(';'))

        # Initialize variables for tracking if the mp3 file has been saved and its name
        mp3_saved = False
        mp3_filename = ""

        for result in interval_results:
            species = result[0]
            confidence_score = float(result[1])

            # Split the species name into scientific and common names
            scientific_name, common_name = species.split('_', 1)

            # figure out what we're supposed to do with a detection of this species
            detectionaction = getaction(scientific_name)

            if (confidence_score > confidence_target) and (detectionaction == 'ignore'):
                print("Detected and ignoring: " + common_name, flush=True)

            # ignore if we're supposed to ignore
            if (confidence_score > confidence_target) and (detectionaction != 'ignore'):
                # Trim the wav file to the interval and save as mp3 if not already saved
                print("Detected: " + common_name + " Action: " + detectionaction, flush=True)

                # only save mp3 if acton is record or alert
                if (not mp3_saved) and (detectionaction == 'record' or detectionaction == 'alert'):
                    # Generate a UUID for the mp3 filename

                    recordinglength = int(preferences['recordinglength'])
                    extractionlength = int(preferences['extractionlength'])
                    spacelength = (extractionlength - 3)/2
                    startwithspace = start_time - spacelength
                    if startwithspace < 0:
                        startwithspace = 0
                    endwithspace = end_time + spacelength
                    if endwithspace > recordinglength:
                        endwithspace = recordinglength

                    mp3_filename = f"{str(uuid.uuid4())}.mp3"
                    trimmed_audio = wav_audio[int(startwithspace * 1000):int(endwithspace * 1000)]
                    trimmed_audio.export(DETECTION_DIR + "/" + mp3_filename, format="mp3")
                    mp3_saved = True

                # Call add_detection with the mp3_filename
                timestamp = recording_metadata['timestamp']
                stream_id = recording_metadata['stream_id']
                streamname = recording_metadata['streamname']

                # don't store an mp3 file name if detectionaction is 'log' even if there happens to already be a recording
                # from this interval
                if detectionaction == 'log':
                    add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence_score,
                                  '')
                else: # if detection action is record or alert
                    add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence_score,
                              mp3_filename)

                if detectionaction == 'alert':
                    # to be replaced when alert functionality is added
                    print('Oh my god its a ' + scientific_name + ' better known as a ' + common_name)


@shared_task()
def analyze_recordings():

    app = current_app._get_current_object()
    celery = app.celery

    # create the detection dir too
    if not os.path.exists(DETECTION_DIR):
        os.makedirs(DETECTION_DIR)

    preferences = get_all_user_preferences(0)

    # This loop will look for wav files, analyze them, sleep a bit and then do it again
    while True:
        # Get all .wav files in the directory

        wav_files = glob.glob(os.path.join(TEMP_DIR, '*.wav'))

        # Sort the files by creation time (oldest first)
        sorted_wav_files = sorted(wav_files, key=os.path.getctime)

        # Iterate through the sorted files
        for file_path in sorted_wav_files:
            filename = os.path.basename(file_path)
            recording_metadata = get_metadata_by_filename(filename)

            if recording_metadata is None:
                # Check if the file is older than 5 minutes
                file_creation_time = os.path.getctime(file_path)
                current_time = time.time()
                time_difference_in_seconds = current_time - file_creation_time
                time_difference_in_minutes = time_difference_in_seconds / 60

                if time_difference_in_minutes > 5:
                    # Delete the file
                    os.remove(file_path)
                    print(f"There is no metadata and the file is old. Deleted file: {filename}", flush=True)

            else:

                # analyze that recording
                stream_id = recording_metadata['stream_id']
                streamname = recording_metadata['streamname']
                timestamp = recording_metadata['timestamp']
                filename = recording_metadata['filename']

                # Get the current time
                now = datetime.now()

                # Get the week number
                year, week_number, weekday = now.isocalendar()

                mdata = {'lat': preferences['latitude'],
                         'lon': preferences['longitude'],
                         'week': week_number,
                         'overlap': preferences['overlap'],
                         'sensitivity': preferences['sensitivity'],
                         'sf_thresh': preferences['sf_thresh'],
                         'pmode': 'max',
                         'num_results': 5,
                         'save': False}

                analysis = sendRequest(file_path, json.dumps(mdata))
                if analysis['msg'] == 'success':
                    # print(analysis, flush=True)
                    check_results(analysis['results'], file_path, recording_metadata, preferences)

                    # That file has been analyzed and results stored. Delete it and its metadata record
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    delete_metadata_by_filename(filename)

                else:
                    print('FAIL')

        time.sleep(1)


def process_streams():

    # initialize the table of expected birds
    create_birdsoftheweek_table()
    update_birdsoftheweek_table()

    streams = get_streams_list()

    preferences = get_all_user_preferences(0)

    # Iterate through each stream and create a record_stream task
    tasks = [record_stream.s(stream, preferences) for stream in streams]

    # Add the analyze_recordings task to the list
    tasks.append(analyze_recordings.s())
    # tasks = [analyze_recordings.s()]

    # Run the tasks concurrently
    group(tasks).apply_async()
