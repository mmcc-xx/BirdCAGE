from flask import current_app
from celery import group, shared_task
from celery.result import AsyncResult
from app.views.streams import get_streams_list
import time
from datetime import datetime, timedelta
import os
from pathlib import Path
import ffmpeg
import uuid
from app.models.preferences import get_all_user_preferences
from app.models.detections import add_detection
from app.models.commands import check_command_value, reset_command
from config import ANALYZE_SERVER, ANALYZE_PORT, TEMP_DIR_NAME, DETECTION_DIR_NAME, REDIS_SERVER, REDIS_PORT
import json
import requests
from app.models.recording_metadata import set_metadata, get_metadata_by_filename, delete_metadata_by_filename
import glob
from pydub import AudioSegment
from .filter_functions import update_birdsoftheweek_table, create_birdsoftheweek_table, getaction
import subprocess
from .notify import notify
from .recordingcleanup import recordingcleanup
from .mqttpub import start_mqtt_client, mqttpublish
from redis import Redis
import signal

basedir = os.path.dirname(os.path.abspath(__file__))
DETECTION_DIR = os.path.join(basedir, '..', DETECTION_DIR_NAME)
TEMP_DIR = os.path.join(basedir, '..', TEMP_DIR_NAME)

redis_client = Redis(host=REDIS_SERVER, port=REDIS_PORT, db=1)


def get_youtube_stream_url(youtube_video_url, format_code=None):
    youtube_dl_command = ["youtube-dl", "-g"]

    if format_code:
        youtube_dl_command.extend(["-f", str(format_code)])

    youtube_dl_command.append(youtube_video_url)

    try:
        stream_url = subprocess.check_output(youtube_dl_command).decode("utf-8").strip()
        return stream_url
    except subprocess.CalledProcessError as e:
        print(f"Failed to get YouTube stream URL: {e}", flush=True)
        return None


def record_stream_ffmpeg(stream_url, protocol, transport, seconds, output_filename):
    try:
        if protocol == 'rtsp':
            (
                ffmpeg
                    .input(stream_url, rtsp_transport=transport.lower())
                    .output(output_filename, format='wav', t=seconds, loglevel='warning',
                            ac=1, ar=48000, sample_fmt='s16')
                    .run(capture_stdout=True, capture_stderr=True)
            )

        elif protocol == 'pulse':
            (
                ffmpeg
                    .input(stream_url, f='pulse')
                    .output(output_filename, format='wav', t=seconds, loglevel='warning',
                            ac=1, ar=48000, sample_fmt='s16')
                    .run(capture_stdout=True, capture_stderr=True)
            )

        elif protocol == 'youtube':
            youtube_stream_url = get_youtube_stream_url(stream_url, format_code=91)
            if youtube_stream_url is None:
                return {'status': 'failure', 'error': 'error getting youtube url'}
            (
                ffmpeg
                    .input(youtube_stream_url)
                    .output(output_filename, format='wav', t=seconds, loglevel='warning',
                            ac=1, ar=48000, sample_fmt='s16')
                    .run(capture_stdout=True, capture_stderr=True)
            )
        else:
            (
                ffmpeg
                    .input(stream_url)
                    .output(output_filename, format='wav', t=seconds, loglevel='warning',
                            ac=1, ar=48000, sample_fmt='s16')
                    .run(capture_stdout=True, capture_stderr=True)
            )
        return {'status': 'success', 'filepath': output_filename}
    except ffmpeg.Error as e:
        message = f'Error: {e}'
        if e.stdout:
            message += f'\n stdout: {e.stdout.decode("ASCII")}'
        if e.stderr:
            message += f'\n stderr: {e.stderr.decode("ASCII")}'
        print(message)
        return {'status': 'failure', 'error': str(e)}


@shared_task(bind=True)
def record_stream(self, stream, preferences):
    # indicate that the task is running
    task_id = self.request.id
    redis_client.hset('task_state', f'{task_id}_status', 'running')

    # set up a handler for SIGTERM signals
    sigterm_received = [False]

    # Signal handler function
    def sigterm_handler(signal_number, frame):
        print(f"SIGTERM received for record_stream task {task_id}, stopping...", flush=True)
        sigterm_received[0] = True

    signal.signal(signal.SIGTERM, sigterm_handler)

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

    # initialize success/fail counters
    consecutive_successes = 0
    consecutive_fails = 0
    redis_client.hset(task_id, 'task_name', 'record_stream_' + name)

    while True:

        try:
            # check for revocation
            task_status = AsyncResult(task_id).status
            if task_status == 'REVOKED':
                print("record_stream for " + name + " has been revoked", flush=True)
                break

            # check for sigterm
            if sigterm_received[0]:
                print("record_stream for " + name + " got a sigterm", flush=True)
                break

            # check for signal to stop
            should_stop = redis_client.hget('task_state', f'{task_id}_stop')
            if should_stop and should_stop.decode() == 'True':
                print("record_stream for " + name + " got signal to stop", flush=True)
                break

            # Generate a unique temporary filename
            tmp_filename = TEMP_DIR + f'/{uuid.uuid4().hex}.wav'

            # Record the stream for 15 seconds and save it to the output file
            result = record_stream_ffmpeg(address, protocol, transport, seconds, tmp_filename)

            if result['status'] == 'success':
                # The recording was successful
                print(f"Recording successful. File saved to: {result['filepath']} Now setting metadata", flush=True)
                set_metadata(os.path.basename(tmp_filename),
                             stream_id, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print(f"Metadata set for: {result['filepath']}", flush=True)

            else:
                # The recording failed
                print(f"Recording failed. Error: {result['error']}")

            consecutive_successes += 1
            consecutive_fails = 0

            redis_client.hset(task_id, 'last_iteration_status', 'success')
            redis_client.hset(task_id, 'consecutive_successes', consecutive_successes)
            # Sleep for some time before recording the stream again
            time.sleep(1)

        except Exception as e:
            print(f"An exception occurred in record_stream for {name}: {e}")
            consecutive_successes = 0
            consecutive_fails += 1

            redis_client.hset(task_id, 'last_iteration_status', 'failed')
            redis_client.hset(task_id, 'consecutive_fails', consecutive_fails)
            redis_client.hset(task_id, 'last_exception', str(e))
            redis_client.hset(task_id, 'last_exception_timestamp', time.time())

            time.sleep(1)


    # we'll only get here if while loop has been break'ed. Indicate that task is stopped
    redis_client.hset('task_state', f'{task_id}_status', 'stopped')
    # and delete the task_id has
    redis_client.delete(task_id)


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
        # print("Returned Data: " + response.text)

        return data
    except Exception:
        return {'msg': 'fail'}


def check_results(results, filepath, recording_metadata, preferences, mqttclient):
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

                mp3path = ''
                # only save mp3 if acton is record or alert
                if (not mp3_saved) and (detectionaction == 'record' or detectionaction == 'alert'):
                    # Generate a UUID for the mp3 filename

                    recordinglength = int(preferences['recordinglength'])
                    extractionlength = int(preferences['extractionlength'])
                    spacelength = (extractionlength - 3) / 2
                    startwithspace = start_time - spacelength
                    if startwithspace < 0:
                        startwithspace = 0
                    endwithspace = end_time + spacelength
                    if endwithspace > recordinglength:
                        endwithspace = recordinglength

                    mp3_filename = f"{str(uuid.uuid4())}.mp3"
                    mp3path = DETECTION_DIR + "/" + mp3_filename
                    trimmed_audio = wav_audio[int(startwithspace * 1000):int(endwithspace * 1000)]
                    trimmed_audio.export(mp3path, format="mp3")
                    mp3_saved = True

                # Call add_detection with the mp3_filename
                timestamp = recording_metadata['timestamp']
                stream_id = recording_metadata['stream_id']
                streamname = recording_metadata['streamname']

                # don't store an mp3 file name if detectionaction is 'log' even if there happens to already be a recording
                # from this interval
                if detectionaction == 'log':
                    print("Adding detection", flush=True)
                    add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence_score,
                                  '')
                    print("Detection added", flush=True)

                else:  # if detection action is record or alert
                    print("Adding detection", flush=True)
                    add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence_score,
                                  mp3_filename)
                    print("Detection added", flush=True)

                notify(detectionaction, timestamp, stream_id, streamname, scientific_name, common_name,
                       confidence_score, mp3path)

                mqttpublish(mqttclient, preferences, detectionaction, timestamp,
                            streamname, scientific_name, common_name,
                            confidence_score, mp3path)


@shared_task(bind=True)
def analyze_recordings(self):
    # indicate that the task is a-runnin'
    task_id = self.request.id
    redis_client.hset('task_state', f'{task_id}_status', 'running')

    # set up a handler for SIGTERM signals
    sigterm_received = [False]

    # Signal handler function
    def sigterm_handler(signal_number, frame):
        print(f"SIGTERM received for analyze_recordings, stopping...", flush=True)
        sigterm_received[0] = True

    signal.signal(signal.SIGTERM, sigterm_handler)

    # create the detection dir too
    if not os.path.exists(DETECTION_DIR):
        os.makedirs(DETECTION_DIR)

    preferences = get_all_user_preferences(0)
    last_cleanup_time = datetime.now()
    last_keepalive_time = datetime.now()

    # start the mqtt client
    mqttclient = start_mqtt_client(preferences)

    # initialize success/fail counters
    consecutive_successes = 0
    consecutive_fails = 0
    redis_client.hset(task_id, 'task_name', 'analyze_recordings')

    # This loop will look for wav files, analyze them, sleep a bit and then do it again
    while True:
        try:
            # check for revocation
            task_status = AsyncResult(task_id).status
            if task_status == 'REVOKED':
                print("Analyze_recordings has been revoked", flush=True)
                break

            # check for sigterm
            if sigterm_received[0]:
                print("analyze_recordings got a sigterm", flush=True)
                break

            # check for signal to stop
            should_stop = redis_client.hget('task_state', f'{task_id}_stop')
            if should_stop and should_stop.decode() == 'True':
                print("analyze_recordings got signal to stop", flush=True)
                break

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
                             'locale': preferences['locale'],
                             'save': False}

                    analysis = sendRequest(file_path, json.dumps(mdata))
                    if analysis['msg'] == 'success':
                        # print(analysis, flush=True)
                        check_results(analysis['results'], file_path, recording_metadata, preferences, mqttclient)

                        # That file has been analyzed and results stored. Delete it and its metadata record
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        print("Deleting metadata", flush=True)
                        delete_metadata_by_filename(filename)
                        print("Metadata deleted", flush=True)

                    else:
                        print('FAIL')

            # Clean up recordings once per day.
            if (datetime.now() - last_cleanup_time) > timedelta(days=1):
                recording_retention = float(preferences['recordingretention'])
                if recording_retention > 0:
                    # Call the recordingcleanup function and update the last_cleanup_time
                    recordingcleanup(recording_retention)

                # this is also a good time to update the birds o the week
                update_birdsoftheweek_table()

                # get new last_cleanup_time
                last_cleanup_time = datetime.now()

            consecutive_successes += 1
            consecutive_fails = 0

            redis_client.hset(task_id, 'last_iteration_status', 'success')
            redis_client.hset(task_id, 'consecutive_successes', consecutive_successes)
            # Sleep for some time before recording the stream again
            time.sleep(1)

        except Exception as e:
            print(f"An exception occurred in analyze_recordings: {e}", flush=True)
            consecutive_successes = 0
            consecutive_fails += 1

            redis_client.hset(task_id, 'last_iteration_status', 'failed')
            redis_client.hset(task_id, 'consecutive_fails', consecutive_fails)
            redis_client.hset(task_id, 'last_exception', str(e))
            redis_client.hset(task_id, 'last_exception_timestamp', time.time())

            time.sleep(1)

    print("Existing analyze_recordings", flush=True)
    # we'll only get here if while loop has been break'ed. Indicate that task is stopped
    redis_client.hset('task_state', f'{task_id}_status', 'stopped')
    # and delete the task_id has
    redis_client.delete(task_id)


@shared_task(bind=True)
def monitor_tasks(self, task_ids):
    def all_tasks_stopped():
        for task_id in task_ids:
            task_status = redis_client.hget('task_state', f'{task_id}_status').decode()
            if task_status != 'stopped':
                return False
        return True

    def cleanup_task_keys():
        for task_id in task_ids:
            redis_client.hdel('task_state', f'{task_id}_status')
            redis_client.hdel('task_state', f'{task_id}_stop')

    # get task ID for monitor_tasks
    mt_task_id = self.request.id

    # set up a handler for SIGTERM signals
    sigterm_received = [False]

    # Signal handler function
    def sigterm_handler(signal_number, frame):
        print(f"SIGTERM received for monitor_tasks, stopping...", flush=True)
        sigterm_received[0] = True

    signal.signal(signal.SIGTERM, sigterm_handler)

    print("Starting monitor_tasks", flush=True)

    task_id = self.request.id
    redis_client.set('monitor_task_id', task_id)

    # initialize success/fail counters
    consecutive_successes = 0
    consecutive_fails = 0
    redis_client.hset(task_id, 'task_name', 'monitor_tasks')

    while True:
        try:

            # check for revocation
            task_status = AsyncResult(mt_task_id).status
            if task_status == 'REVOKED':
                print("monitor_tasks has been revoked", flush=True)
                cleanup_task_keys()
                break

                # check for sigterm
            if sigterm_received[0]:
                print("monitor_tasks got a sigterm", flush=True)
                cleanup_task_keys()
                break

            # Periodically check the status of the tasks
            time.sleep(2)

            # Check to see if we've gotten a restart signal
            if check_command_value('restart'):
                # Ask all the tasks to stop
                for task_id in task_ids:
                    redis_client.hset('task_state', f'{task_id}_stop', 'True')

                    # Wait for all tasks to stop
                while not all_tasks_stopped():
                    print("Waiting for tasks to stop", flush=True)
                    time.sleep(1)

                print("Tasks stopped. Restarting", flush=True)
                cleanup_task_keys()

                # Restart the tasks
                new_task_ids = start_tasks()

                # Update the task_ids variable to monitor the new tasks
                task_ids = new_task_ids

                # reset the command from the UI
                reset_command('restart', False)

            consecutive_successes += 1
            consecutive_fails = 0

            redis_client.hset(task_id, 'last_iteration_status', 'success')
            redis_client.hset(task_id, 'consecutive_successes', consecutive_successes)

        except Exception as e:
            print(f"An exception occurred in monitor_tasks: {e}", flush=True)
            consecutive_successes = 0
            consecutive_fails += 1

            redis_client.hset(task_id, 'last_iteration_status', 'failed')
            redis_client.hset(task_id, 'consecutive_fails', consecutive_fails)
            redis_client.hset(task_id, 'last_exception', str(e))
            redis_client.hset(task_id, 'last_exception_timestamp', time.time())

            time.sleep(2)


def start_tasks():
    print('Starting recording and analyze tasks', flush=True)
    streams = get_streams_list()
    preferences = get_all_user_preferences(0)

    tasks = [record_stream.s(stream, preferences) for stream in streams]
    tasks.append(analyze_recordings.s())
    task_group = group(tasks)
    results = task_group.apply_async()
    task_ids = [result.id for result in results.children]

    # write the task IDs to redis
    redis_client.delete('task_ids')
    for task_id in task_ids:
        redis_client.sadd('task_ids', task_id)
    return task_ids


def process_streams():
    # initialize the table of expected birds
    create_birdsoftheweek_table()
    update_birdsoftheweek_table()

    task_ids = start_tasks()
    # Start the monitor_tasks task
    monitor_tasks.apply_async(args=[task_ids])
