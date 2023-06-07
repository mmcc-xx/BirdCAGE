from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE
from app.decorators import admin_required

commands_blueprint = Blueprint('commands', __name__)


def query_db(query, args=(), one=False):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute(query, args)
    results = cursor.fetchall()
    connection.close()

    return (results[0] if results else None) if one else results


@commands_blueprint.route('/api/command/<command_name>', methods=['GET'])
def get_command(command_name):
    command = query_db('SELECT * FROM commands WHERE name = ?', (command_name,), one=True)
    if command:
        return jsonify({'id': command[0], 'name': command[1], 'value': bool(command[2])})
    else:
        return jsonify({'error': 'Command not found'}), 404


@commands_blueprint.route('/api/command/<command_name>', methods=['PUT'])
@admin_required
def set_command_value(command_name):
    if 'value' not in request.json:
        return jsonify({'error': 'Value not provided'}), 400

    value = request.json['value']

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute('UPDATE commands SET value = ? WHERE name = ?', (value, command_name))

    if cursor.rowcount == 0:
        connection.close()
        return jsonify({'error': 'Command not found'}), 404

    connection.commit()
    connection.close()

    return jsonify({'success': True, 'name': command_name, 'value': value})
