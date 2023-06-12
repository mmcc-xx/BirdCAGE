import paho.mqtt.client as mqtt
import time
import json
import base64
from .filter_functions import get_birdsoftheweek


def on_connect(client, userdata, flags, rc):
    print("Connected to the broker with result code: " + str(rc), flush=True)


def on_disconnect(client, userdata, rc):
    print("Disconnected from the broker with result code: " + str(rc), flush=True)
    if rc != 0:
        print("Unexpected disconnection. Paho should be trying reconnect", flush=True)


def on_publish(client, userdata, mid):
    print("Message published with mid: " + str(mid), flush=True)


def start_mqtt_client(preferences):
    if preferences['mqttbroker'] == '':
        return None

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    mqttbroker = preferences['mqttbroker']
    mqttport = int(preferences['mqttport'])
    mqttuser = preferences['mqttuser']
    mqttpassword = preferences['mqttpassword']

    while True:
        try:
            if mqttuser != '':
                client.username_pw_set(mqttuser, mqttpassword)
            client.connect(mqttbroker, mqttport, 60)
            break
        except Exception as e:
            print("Failed to connect to MQTT broker, trying again in 1 minute...", flush=True)
            print(f"Error: {e}", flush=True)
            time.sleep(60)

    client.loop_start()
    return client


def mqttpublish(client, preferences, detectionaction, timestamp, streamname, scientific_name, common_name,
                       confidence_score, mp3path):

    if client is None:
        print("MQTT not being used. Skipping publication.", flush=True)
        return

    includemp3 = preferences['mqttrecordings']
    mqtttopic = "BirdCAGE/" + detectionaction + "/" + streamname

    birdsoftheweek = get_birdsoftheweek()
    occurrence = birdsoftheweek.get(scientific_name, {}).get('occurrence', 0)

    payload = {
        "CommonName": common_name,
        "ScientificName": scientific_name,
        "ConfidenceScore": confidence_score,
        "TimeStamp": timestamp,
        "StreamName": streamname,
        "ImportanceLevel": detectionaction,
        "Occurrence": occurrence
    }

    print("Publishing to " + mqtttopic + " about a " + common_name)

    if includemp3 == 'true' and mp3path != '':
        print("Publication includes MP3")
        with open(mp3path, 'rb') as mp3file:
            mp3_data = mp3file.read()
        payload["MP3"] = base64.b64encode(mp3_data).decode('utf-8')

    client.publish(mqtttopic, json.dumps(payload), retain=True)
