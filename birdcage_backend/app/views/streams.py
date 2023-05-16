from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE


streams_blueprint = Blueprint('streams', __name__)


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
def delete_stream(stream_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('DELETE FROM streams WHERE id = ?', (stream_id,))

    connection.commit()
    connection.close()

    return jsonify({"message": "Stream deleted successfully."})
