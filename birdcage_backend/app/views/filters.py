from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime
from config import DATABASE_FILE, ANALYZE_SERVER, ANALYZE_PORT
from app.models.preferences import get_all_user_preferences
import requests
from app.decorators import admin_required

filters_blueprint = Blueprint('filters', __name__)


@filters_blueprint.route('/api/filters/birdsoftheweek', methods=['GET'])
def get_birds_of_the_week():

    #get the predicted birds of the week from BirdNET Analyzer and return to client
    url = 'http://{}:{}/predictedspecies'.format(ANALYZE_SERVER, ANALYZE_PORT)

    preferences = get_all_user_preferences(0)
    now = datetime.now()
    year, week_number, weekday = now.isocalendar()

    response = requests.get(url, params={
        'latitude': preferences['latitude'],
        'longitude': preferences['longitude'],
        'week_number': week_number,
        'locale': preferences['locale'],
        'sf_thresh': preferences['sf_thresh']
    })

    return response.json()


@filters_blueprint.route('/api/filters/thresholds/<int:user_id>', methods=['GET'])
def get_thresholds(user_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT ignore_threshold, log_threshold, recordalert_threshold FROM filter_thresholds WHERE user_id = ?;",
        (user_id,))
    thresholds = cursor.fetchone()

    connection.close()

    if thresholds:
        return jsonify(
            {"ignore_threshold": thresholds[0], "log_threshold": thresholds[1], "recordalert_threshold": thresholds[2]})
    else:
        return jsonify({"error": "User not found"}), 404


@filters_blueprint.route('/api/filters/thresholds/<int:user_id>', methods=['POST'])
@admin_required
def set_thresholds(user_id):
    try:
        ignore_threshold = float(request.form['ignore_threshold'])
        log_threshold = float(request.form['log_threshold'])
        recordalert_threshold = float(request.form['recordalert_threshold'])
    except ValueError:
        return jsonify({"error": "Invalid input"}), 400

    if not (0 <= ignore_threshold >= log_threshold >= recordalert_threshold >= 0 and ignore_threshold <= 1):
        return jsonify({"error": "Invalid threshold values"}), 400

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO filter_thresholds (user_id, ignore_threshold, log_threshold, recordalert_threshold) VALUES (?, ?, ?, ?);",
        (user_id, ignore_threshold, log_threshold, recordalert_threshold))

    connection.commit()
    connection.close()

    return jsonify({"success": "Thresholds updated"})


@filters_blueprint.route('/api/filters/overrides/<int:user_id>', methods=['GET'])
def get_overrides(user_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT species_name, override_type FROM species_overrides WHERE user_id = ?;", (user_id,))
    overrides = cursor.fetchall()

    connection.close()

    return jsonify([{"species_name": override[0], "override_type": override[1]} for override in overrides])


@filters_blueprint.route('/api/filters/overrides/<int:user_id>', methods=['POST', 'DELETE'])
@admin_required
def add_remove_override(user_id):
    species_name = request.form['species_name']

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    if request.method == 'POST':
        override_type = request.form['override_type']
        if override_type not in ["ignore", "log", "record", "alert"]:
            return jsonify({"error": "Invalid override type"}), 400

        try:
            cursor.execute("INSERT INTO species_overrides (user_id, species_name, override_type) VALUES (?, ?, ?);",
                           (user_id, species_name, override_type))
            connection.commit()
            return jsonify({"success": "Override added"})
        except sqlite3.IntegrityError:
            return jsonify({"error": "Override already exists"}), 400

    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM species_overrides WHERE user_id = ? AND species_name = ?;", (user_id, species_name))
        connection.commit()

        if cursor.rowcount > 0:
            return jsonify({"success": "Override removed"})
        else:
            return jsonify({"error": "Override not found"}), 404

    connection.close()
