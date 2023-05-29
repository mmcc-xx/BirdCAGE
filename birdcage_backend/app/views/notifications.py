from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE
from app.decorators import admin_required

notifications_blueprint = Blueprint('notifications', __name__)


def get_db_connection():
    return sqlite3.connect(DATABASE_FILE)


# Get all of the notification services and URLs from notification_services
@notifications_blueprint.route('/services', methods=['GET'])
def get_notification_services():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT service_name, service_url FROM notification_services')
    services = cursor.fetchall()
    connection.close()

    response = [{'service_name': service[0], 'service_url': service[1]} for service in services]
    return jsonify(response)


# Set the URL for a notification service from notification_services
@notifications_blueprint.route('/services/<service_name>', methods=['PUT'])
@admin_required
def set_notification_service_url(service_name):
    service_url = request.json.get('service_url', '')
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE notification_services SET service_url = ? WHERE service_name = ?',
                   (service_url, service_name))
    connection.commit()
    connection.close()

    return jsonify({'result': 'success', 'message': 'Service URL updated'})


# Get all of the detection actions and associated notification services from notification_assignments
@notifications_blueprint.route('/assignments', methods=['GET'])
def get_detection_assignments():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT detectionaction, notification_service FROM notification_assignments')
    assignments = cursor.fetchall()
    connection.close()

    response = [{'detection_action': assignment[0], 'notification_service': assignment[1]} for assignment in
                assignments]
    return jsonify(response)


# Add a specified notification service for a particular detection action in notification_assignments
@notifications_blueprint.route('/assignments', methods=['POST'])
@admin_required
def add_detection_assignment():
    detection_action = request.json.get('detection_action')
    notification_service = request.json.get('notification_service')

    if not detection_action or not notification_service:
        return jsonify({'result': 'error', 'message': 'Missing detection_action or notification_service'})

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO notification_assignments (detectionaction, notification_service) VALUES (?, ?)',
        (detection_action, notification_service))
    connection.commit()
    connection.close()

    return jsonify({'result': 'success', 'message': 'Detection assignment added'})


# Remove a specified notification service for a particular detection action in notification_assignments
@notifications_blueprint.route('/assignments', methods=['DELETE'])
@admin_required
def remove_detection_assignment():
    detection_action = request.json.get('detection_action')
    notification_service = request.json.get('notification_service')

    if not detection_action or not notification_service:
        return jsonify({'result': 'error', 'message': 'Missing detection_action or notification_service'})

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM notification_assignments WHERE detectionaction = ? AND notification_service = ?',
                   (detection_action, notification_service))
    connection.commit()
    connection.close()

    return jsonify({'result': 'success', 'message': 'Detection assignment removed'})
