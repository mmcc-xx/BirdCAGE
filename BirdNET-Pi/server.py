import re
from pathlib import Path
from tzlocal import get_localzone
import datetime
import sqlite3
import requests
import json
import time
import socket
import threading
import os
import gzip

from utils.notifications import sendAppriseNotifications
from utils.parse_settings import config_to_settings

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

HEADER = 64
PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
ANALYSIS_SERVER = "192.168.1.75"
ANALYSIS_PORT = "7667"

userDir = os.path.expanduser('~')
DB_PATH = userDir + '/BirdNET-Pi/scripts/birds.db'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server.bind(ADDR)
except BaseException:
    print("Waiting on socket")
    time.sleep(5)


# Open most recent Configuration and grab DB_PWD as a python variable
with open(userDir + '/BirdNET-Pi/scripts/thisrun.txt', 'r') as f:
    this_run = f.readlines()
    audiofmt = "." + str(str(str([i for i in this_run if i.startswith('AUDIOFMT')]).split('=')[1]).split('\\')[0])
    priv_thresh = float("." + str(str(str([i for i in this_run if i.startswith('PRIVACY_THRESHOLD')]).split('=')[1]).split('\\')[0])) / 10
    try:
        model = str(str(str([i for i in this_run if i.startswith('MODEL')]).split('=')[1]).split('\\')[0])
        sf_thresh = str(str(str([i for i in this_run if i.startswith('SF_THRESH')]).split('=')[1]).split('\\')[0])
    except Exception as e:
        model = "BirdNET_6K_GLOBAL_MODEL"
        sf_thresh = 0.03


def loadCustomSpeciesList(path):

    slist = []
    if os.path.isfile(path):
        with open(path, 'r') as csfile:
            for line in csfile.readlines():
                slist.append(line.replace('\r', '').replace('\n', ''))

    return slist


def writeResultsToFile(detections, min_conf, path):

    print('WRITING RESULTS TO', path, '...', end=' ')
    rcnt = 0
    with open(path, 'w') as rfile:
        rfile.write('Start (s);End (s);Scientific name;Common name;Confidence\n')

        for interval in detections["results"]:
            for result in detections['results'][interval]:
                species = result[0]  # Get the species name from the first element of the sublist
                print("Species: " + species)
                confidence = result[1]  # Get the confidence level from the second element of the sublist
                print("Confidence: " + str(confidence))
                if confidence >= min_conf and ((species in INCLUDE_LIST or len(INCLUDE_LIST) == 0) and (species not in EXCLUDE_LIST or len(EXCLUDE_LIST) == 0) ):
                    rfile.write(interval + ';' + species.replace('_', ';').split("/")[0] + ';' + str(confidence) + '\n')
                    rcnt += 1

    print('DONE! WROTE', rcnt, 'RESULTS.')
    return


def sendRequest(host, port, fpath, mdata):
    url = 'http://{}:{}/analyze'.format(host, port)

    # print('Requesting analysis for {}'.format(fpath))

    # Make payload
    multipart_form_data = {
        'audio': (fpath.split(os.sep)[-1], open(fpath, 'rb')),
        'meta': (None, mdata)
    }

    # Send request
    start_time = time.time()
    response = requests.post(url, files=multipart_form_data)
    end_time = time.time()

    print('Response: {}, Time: {:.4f}s'.format(response.text, end_time - start_time), flush=True)

    # Convert to dict
    data = json.loads(response.text)

    return data


def handle_client(conn, addr):
    global INCLUDE_LIST
    global EXCLUDE_LIST
    # print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            else:
                # print(f"[{addr}] {msg}")

                args = type('', (), {})()

                args.i = ''
                args.o = ''
                args.birdweather_id = '99999'
                args.include_list = 'null'
                args.exclude_list = 'null'
                args.overlap = 0.0
                args.week = -1
                args.sensitivity = 1.25
                args.min_conf = 0.70
                args.lat = -1
                args.lon = -1

                for line in msg.split('||'):
                    inputvars = line.split('=')
                    if inputvars[0] == 'i':
                        args.i = inputvars[1]
                    elif inputvars[0] == 'o':
                        args.o = inputvars[1]
                    elif inputvars[0] == 'birdweather_id':
                        args.birdweather_id = inputvars[1]
                    elif inputvars[0] == 'include_list':
                        args.include_list = inputvars[1]
                    elif inputvars[0] == 'exclude_list':
                        args.exclude_list = inputvars[1]
                    elif inputvars[0] == 'overlap':
                        args.overlap = float(inputvars[1])
                    elif inputvars[0] == 'week':
                        args.week = int(inputvars[1])
                    elif inputvars[0] == 'sensitivity':
                        args.sensitivity = float(inputvars[1])
                    elif inputvars[0] == 'min_conf':
                        args.min_conf = float(inputvars[1])
                    elif inputvars[0] == 'lat':
                        args.lat = float(inputvars[1])
                    elif inputvars[0] == 'lon':
                        args.lon = float(inputvars[1])

                # Load custom species lists - INCLUDED and EXCLUDED
                if not args.include_list == 'null':
                    INCLUDE_LIST = loadCustomSpeciesList(args.include_list)
                else:
                    INCLUDE_LIST = []

                if not args.exclude_list == 'null':
                    EXCLUDE_LIST = loadCustomSpeciesList(args.exclude_list)
                else:
                    EXCLUDE_LIST = []

                birdweather_id = args.birdweather_id

                # Get Date/Time from filename in case Pi gets behind
                # now = datetime.now()
                full_file_name = args.i
                # print('FULL FILENAME: -' + full_file_name + '-')
                file_name = Path(full_file_name).stem

                # Get the RSTP stream identifier from the filename if it exists
                RTSP_ident_for_fn = ""
                RTSP_ident = re.search("RTSP_[0-9]+-", file_name)
                if RTSP_ident is not None:
                    RTSP_ident_for_fn = RTSP_ident.group()

                # Find and remove the identifier for the RSTP stream url it was from that is added when more than one
                # RSTP stream is recorded simultaneously, in order to make the filenames unique as filenames are all
                # generated at the same time
                file_name = re.sub("RTSP_[0-9]+-", "", file_name)

                # Now we can read the date and time as normal
                # First portion of the filename contaning the date in Y m d
                file_date = file_name.split('-birdnet-')[0]
                # Second portion of the filename containing the time in H:M:S
                file_time = file_name.split('-birdnet-')[1]
                # Join the date and time together to get a complete string representing when the audio was recorded
                date_time_str = file_date + ' ' + file_time
                date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
                # print('Date:', date_time_obj.date())
                # print('Time:', date_time_obj.time())
                print('Date-time:', date_time_obj)
                now = date_time_obj
                current_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")
                current_iso8601 = now.astimezone(get_localzone()).isoformat()

                week_number = int(now.strftime("%V"))
                week = max(1, min(week_number, 48))

                sensitivity = max(0.5, min(1.0 - (args.sensitivity - 1.0), 1.5))

                mdata = {'lat': args.lat,
                         'lon': args.lon,
                         'week': week,
                         'overlap': args.overlap,
                         'sensitivity': sensitivity,
                         'pmode': 'max'
                         }
                detections = sendRequest(ANALYSIS_SERVER, ANALYSIS_PORT, args.i, json.dumps(mdata))

                # Write detections to output file
                min_conf = max(0.01, min(args.min_conf, 0.99))
                writeResultsToFile(detections, min_conf, args.o)

            ###############################################################################
            ###############################################################################

                soundscape_uploaded = False

                # Write detections to Database
                myReturn = ''
                for interval in detections["results"]:
                    for result in detections["results"][interval]:
                        #myReturn += str(i) + '-' + str(detections[i][0]) + '\n'
                        species = result[0]
                        myReturn += interval + '-' + species + '\n'

                    with open(userDir + '/BirdNET-Pi/BirdDB.txt', 'a') as rfile:
                        species_apprised_this_run = []
                        for result in detections["results"][interval]:
                            species = result[0]  # Get the species name from the first element of the sublist
                            print("Species: " + species)
                            confidence = result[1]  # Get the confidence level from the second element of the sublist
                            print("Confidence: " + str(confidence))

                            if confidence >= min_conf and ((species in INCLUDE_LIST or len(INCLUDE_LIST) == 0)
                                                         and (species not in EXCLUDE_LIST or len(EXCLUDE_LIST) == 0) ):
                                # Write to text file.
                                rfile.write(str(current_date) + ';' + str(current_time) + ';' + species.replace('_', ';').split("/")[0] + ';'
                                            + str(confidence) + ";" + str(args.lat) + ';' + str(args.lon) + ';' + str(min_conf) + ';' + str(week) + ';'
                                            + str(args.sensitivity) + ';' + str(args.overlap) + '\n')

                                # Write to database
                                Date = str(current_date)
                                Time = str(current_time)
                                species2 = species.split("/")[0]
                                Sci_Name, Com_Name = species2.split('_')
                                score = confidence
                                Confidence2 = str(round(score * 100))
                                Lat = str(args.lat)
                                Lon = str(args.lon)
                                Cutoff = str(args.min_conf)
                                Week = str(args.week)
                                Sens = str(args.sensitivity)
                                Overlap = str(args.overlap)
                                Com_Name = Com_Name.replace("'", "")
                                File_Name = Com_Name.replace(" ", "_") + '-' + Confidence2 + '-' + \
                                    Date.replace("/", "-") + '-birdnet-' + RTSP_ident_for_fn + Time + audiofmt

                                # Connect to SQLite Database
                                for attempt_number in range(3):
                                    try:
                                        con = sqlite3.connect(DB_PATH)
                                        cur = con.cursor()
                                        cur.execute("INSERT INTO detections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (Date, Time,
                                                    Sci_Name, Com_Name, str(score), Lat, Lon, Cutoff, Week, Sens, Overlap, File_Name))

                                        con.commit()
                                        con.close()
                                        break
                                    except BaseException:
                                        print("Database busy")
                                        time.sleep(2)

                                # Apprise of detection if not already alerted this run.
                                if not species in species_apprised_this_run:
                                    settings_dict = config_to_settings(userDir + '/BirdNET-Pi/scripts/thisrun.txt')
                                    sendAppriseNotifications(species2,
                                                             str(score),
                                                             File_Name,
                                                             Date,
                                                             Time,
                                                             Week,
                                                             Lat,
                                                             Lon,
                                                             Cutoff,
                                                             Sens,
                                                             Overlap,
                                                             settings_dict,
                                                             DB_PATH)
                                    species_apprised_this_run.append(species)

                                print(str(current_date) +
                                      ';' +
                                      str(current_time) +
                                      ';' +
                                      species.replace('_', ';') +
                                      ';' +
                                      str(confidence) +
                                      ';' +
                                      str(args.lat) +
                                      ';' +
                                      str(args.lon) +
                                      ';' +
                                      str(min_conf) +
                                      ';' +
                                      str(week) +
                                      ';' +
                                      str(args.sensitivity) +
                                      ';' +
                                      str(args.overlap) +
                                      ';' +
                                      File_Name +
                                      '\n')

                                if birdweather_id != "99999":
                                    try:

                                        if soundscape_uploaded is False:
                                            # POST soundscape to server
                                            soundscape_url = 'https://app.birdweather.com/api/v1/stations/' + \
                                                birdweather_id + \
                                                '/soundscapes' + \
                                                '?timestamp=' + \
                                                current_iso8601

                                            with open(args.i, 'rb') as f:
                                                wav_data = f.read()
                                            gzip_wav_data = gzip.compress(wav_data)
                                            response = requests.post(url=soundscape_url, data=gzip_wav_data, headers={'Content-Type': 'application/octet-stream',
                                                                                                                      'Content-Encoding': 'gzip'})
                                            print("Soundscape POST Response Status - ", response.status_code)
                                            sdata = response.json()
                                            soundscape_id = sdata['soundscape']['id']
                                            soundscape_uploaded = True

                                        # POST detection to server
                                        detection_url = "https://app.birdweather.com/api/v1/stations/" + birdweather_id + "/detections"
                                        start_time = interval.split(';')[0]
                                        end_time = interval.split(';')[1]
                                        post_begin = "{ "
                                        now_p_start = now + datetime.timedelta(seconds=float(start_time))
                                        current_iso8601 = now_p_start.astimezone(get_localzone()).isoformat()
                                        post_timestamp = "\"timestamp\": \"" + current_iso8601 + "\","
                                        post_lat = "\"lat\": " + str(args.lat) + ","
                                        post_lon = "\"lon\": " + str(args.lon) + ","
                                        post_soundscape_id = "\"soundscapeId\": " + str(soundscape_id) + ","
                                        post_soundscape_start_time = "\"soundscapeStartTime\": " + start_time + ","
                                        post_soundscape_end_time = "\"soundscapeEndTime\": " + end_time + ","
                                        post_commonName = "\"commonName\": \"" + species.split('_')[1].split("/")[0] + "\","
                                        post_scientificName = "\"scientificName\": \"" + species.split('_')[0] + "\","

                                        if model == "BirdNET_GLOBAL_3K_V2.3_Model_FP16":
                                            post_algorithm = "\"algorithm\": " + "\"2p3\"" + ","
                                        else:
                                            post_algorithm = "\"algorithm\": " + "\"alpha\"" + ","

                                        post_confidence = "\"confidence\": " + str(confidence)
                                        post_end = " }"

                                        post_json = post_begin + post_timestamp + post_lat + post_lon + post_soundscape_id + post_soundscape_start_time + \
                                            post_soundscape_end_time + post_commonName + post_scientificName + post_algorithm + post_confidence + post_end
                                        print(post_json)
                                        response = requests.post(detection_url, json=json.loads(post_json))
                                        print("Detection POST Response Status - ", response.status_code)
                                    except BaseException:
                                        print("Cannot POST right now")
                conn.send(myReturn.encode(FORMAT))

                # time.sleep(3)

    conn.close()


def start():
    # Load model
    global INCLUDE_LIST, EXCLUDE_LIST

    print("The BirdNET-Pi Server Begins")
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


# print("[STARTING] server is starting...")
start()
