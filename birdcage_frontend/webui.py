from flask import Flask, render_template
import requests
from datetime import datetime
import os

app = Flask(__name__)

API_SERVER_URL = os.environ.get('API_SERVER_URL', 'http://192.168.1.75:7006')
WEBUI_PORT = os.environ.get('WEBUI_PORT', '7009')

@app.route('/')
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', api_server_url=API_SERVER_URL, today=today)


@app.route('/detections/by_hour/<date>/<int:hour>')
def show_detections_by_hour(date, hour):
    return render_template('detections_by_hour.html', date=date, api_server_url=API_SERVER_URL, hour=hour)


@app.route('/detections/by_common_name/<date>/<common_name>')
def show_detections_by_common_name(date, common_name):
    return render_template('detections_by_name.html', api_server_url=API_SERVER_URL, date=date, common_name=common_name)


@app.route('/daily_summary/<date>')
def daily_summary(date):
    return render_template('daily_summary.html', date=date, api_server_url=API_SERVER_URL)


@app.route('/stream_settings', methods=['GET'])
def streams():
    return render_template('stream_settings.html', api_server_url=API_SERVER_URL)


@app.route('/preferences', methods=['GET'])
def preferences():
    user_id = 0
    response = requests.get(f"{API_SERVER_URL}/api/preferences/{user_id}")
    current_preferences = response.json()
    return render_template('preferences.html', api_server_url=API_SERVER_URL, current_preferences=current_preferences)


@app.route('/detections/detection/<int:detection_id>')
def show_detection_details(detection_id):
    return render_template('detection_details.html', detection_id=detection_id, api_server_url=API_SERVER_URL)


@app.route('/birdsoftheweek')
def birds_of_the_week():
    return render_template('birdsoftheweek.html', api_server_url=API_SERVER_URL)


@app.route('/detectionfilters')
def detectionfilters():
    return render_template('detectionfilters.html', api_server_url=API_SERVER_URL)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(WEBUI_PORT))
