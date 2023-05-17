from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

API_SERVER_URL = "http://birdcageapi.casefamily.audioandoddities.com"


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7008)
