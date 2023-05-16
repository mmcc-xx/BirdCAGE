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

basedir = os.path.dirname(os.path.abspath(__file__))
DETECTION_DIR = os.path.join(basedir, '..', DETECTION_DIR_NAME)
TEMP_DIR = os.path.join(basedir, '..', TEMP_DIR_NAME)

def record_stream_ffmpeg(stream_url, protocol, transport, seconds, output_filename):
    try:
        if protocol == 'rtsp':
            (
                ffmpeg
                .input(stream_url, rtsp_transport=transport.lower())
                .output(output_filename, format='wav', t=seconds)
                .run()
            )
        else:
            (
                ffmpeg
                .input(stream_url)
                .output(output_filename, format='wav', t=seconds)
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
            print(f"Recording successful. File saved to: {result['filepath']}")
            set_metadata(os.path.basename(tmp_filename),
                         stream_id, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        else:
            # The recording failed
            print(f"Recording failed. Error: {result['error']}")

        # Sleep for some time before recording the stream again
        time.sleep(1)


def sendRequest(fpath, mdata):
    url = 'http://{}:{}/analyze'.format(ANALYZE_SERVER, ANALYZE_PORT)

    print('Requesting analysis for {}'.format(fpath))

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
        print(f"Time interval: {time_interval}")
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

            print(
                f"  Scientific name: {scientific_name}, Common name: {common_name}, Confidence score: {confidence_score}",
                flush=True)

            if confidence_score > confidence_target:
                # Trim the wav file to the interval and save as mp3 if not already saved
                if not mp3_saved:
                    # Generate a UUID for the mp3 filename
                    mp3_filename = f"{str(uuid.uuid4())}.mp3"
                    trimmed_audio = wav_audio[int(start_time * 1000):int(end_time * 1000)]
                    trimmed_audio.export(DETECTION_DIR + "/" + mp3_filename, format="mp3")
                    mp3_saved = True

                # Call add_detection with the mp3_filename
                timestamp = recording_metadata['timestamp']
                stream_id = recording_metadata['stream_id']
                streamname = recording_metadata['streamname']
                add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence_score,
                              mp3_filename)


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
                # if there's no metadata the file is of no use. Delete it
                #if os.path.exists(file_path):
                #    os.remove(file_path)
                break

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
                print(analysis, flush=True)
                check_results(analysis['results'], file_path, recording_metadata, preferences)

                # That file has been analyzed and results stored. Delete it an its metadata record
                if os.path.exists(file_path):
                    os.remove(file_path)
                delete_metadata_by_filename(filename)

            else:
                print('FAIL')

        time.sleep(1)


def process_streams():

    streams = get_streams_list()

    preferences = get_all_user_preferences(0)

    # Iterate through each stream and create a record_stream task
    tasks = [record_stream.s(stream, preferences) for stream in streams]

    # Add the analyze_recordings task to the list
    tasks.append(analyze_recordings.s())
    # tasks = [analyze_recordings.s()]

    # Run the tasks concurrently
    group(tasks).apply_async()
