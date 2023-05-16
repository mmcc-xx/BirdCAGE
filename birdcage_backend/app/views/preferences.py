from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE

preferences_blueprint = Blueprint('preferences', __name__)


@preferences_blueprint.route('/api/preferences/<int:user_id>', methods=['GET'])
def get_preferences(user_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?', (user_id,))
    preferences = cursor.fetchall()

    preferences_dict = {key: value for (key, value) in preferences}

    connection.close()

    return jsonify(preferences_dict)


@preferences_blueprint.route('/api/preferences', methods=['POST'])
def set_preference():
    data = request.get_json()

    user_id = data['user_id']
    preference_key = data['preference_key']
    preference_value = data['preference_value']

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, last_updated) VALUES (?, ?, ?, datetime())',
        (user_id, preference_key, preference_value))

    connection.commit()
    connection.close()

    return jsonify({"message": "Preference set successfully."})


@preferences_blueprint.route('/api/preferences/<int:user_id>/<string:preference_key>', methods=['DELETE'])
def delete_preference(user_id, preference_key):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('DELETE FROM user_preferences WHERE user_id = ? AND preference_key = ?', (user_id, preference_key))

    connection.commit()
    connection.close()

    return jsonify({"message": "Preference deleted successfully."})
