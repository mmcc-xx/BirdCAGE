from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE
from ..models.preferences import check_password
from functools import wraps

streams_blueprint = Blueprint('streams', __name__)


def password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password_input = request.headers.get('X-Password')
        if password_input is None:
            return jsonify({"error": "Password header is missing"}), 401
        if not check_password(password_input):
            return jsonify({"error": "Invalid password"}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_streams_list():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM streams')
    streams = cursor.fetchall()

    # Convert the fetched data into a list of dictionaries
    streams_dict = [
        {
            "id": stream[0],
            "name": stream[1],
            "address": stream[2],
            "protocol": stream[3],
            "transport": stream[4],
        }
        for stream in streams
    ]

    connection.close()

    return streams_dict


@streams_blueprint.route('/api/streams', methods=['GET'])
def get_streams():
    streams = get_streams_list()
    return jsonify(streams)


@streams_blueprint.route('/api/streams', methods=['POST'])
@password_required
def create_stream():
    data = request.get_json()

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO streams (name, address, protocol, transport) VALUES (?, ?, ?, ?)',
                   (data['name'], data['address'], data['protocol'], data.get('transport')))

    connection.commit()
    connection.close()

    return jsonify({"message": "Stream created successfully."})


@streams_blueprint.route('/api/streams/<int:stream_id>', methods=['PUT'])
@password_required
def update_stream(stream_id):
    data = request.get_json()

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''UPDATE streams  
                      SET name = ?, address = ?, protocol = ?, transport = ?  
                      WHERE id = ?''',
                   (data['name'], data['address'], data['protocol'], data.get('transport'), stream_id))

    connection.commit()
    connection.close()

    return jsonify({"message": "Stream updated successfully."})


@streams_blueprint.route('/api/streams/<int:stream_id>', methods=['DELETE'])
@password_required
def delete_stream(stream_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('DELETE FROM streams WHERE id = ?', (stream_id,))

    connection.commit()
    connection.close()

    return jsonify({"message": "Stream deleted successfully."})
