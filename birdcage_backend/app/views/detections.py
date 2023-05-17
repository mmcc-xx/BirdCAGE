from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE

detections_blueprint = Blueprint('detections', __name__)


# Get X most recent detections
@detections_blueprint.route('/api/detections/recent/<int:limit>', methods=['GET'])
def get_recent_detections(limit):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM detections ORDER BY timestamp DESC LIMIT ?', (limit,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# Get all of the detections for a given date
@detections_blueprint.route('/api/detections/date/<string:date>', methods=['GET'])
def get_detections_by_date(date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM detections WHERE DATE(timestamp) = ? ORDER BY timestamp ASC', (date,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# Get the total number of detections for a given date
@detections_blueprint.route('/api/detections/date/<string:date>/count', methods=['GET'])
def get_detection_count_by_date(date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM detections WHERE DATE(timestamp) = ?', (date,))
    count = cursor.fetchone()[0]

    connection.close()

    return jsonify({"count": count})


# Number of detections for a given day for unique scientific_names, ascending or descending
@detections_blueprint.route('/api/detections/date/<string:date>/grouped/<string:sort_order>', methods=['GET'])
def get_grouped_detections_by_date(date, sort_order):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    if sort_order not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort order"}), 400

    cursor.execute(
        f'SELECT scientific_name, COUNT(*) as count FROM detections WHERE DATE(timestamp) = ? GROUP BY scientific_name ORDER BY count {sort_order.upper()}',
        (date,))
    grouped_detections = cursor.fetchall()

    connection.close()

    return jsonify(grouped_detections)


# All detections for a given day for a given scientific_name, sorted by confidence descending
@detections_blueprint.route('/api/detections/date/<string:date>/scientific_name/<string:scientific_name>/confidence',
                            methods=['GET'])
def get_detections_by_scientific_name_and_confidence(date, scientific_name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM detections WHERE DATE(timestamp) = ? AND scientific_name = ? ORDER BY confidence DESC',
        (date, scientific_name,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# All detections for a given day for a given scientific_name, sorted by time ascending
@detections_blueprint.route('/api/detections/date/<string:date>/scientific_name/<string:scientific_name>/timestamp',
                            methods=['GET'])
def get_detections_by_scientific_name_and_timestamp(date, scientific_name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM detections WHERE DATE(timestamp) = ? AND scientific_name = ? ORDER BY timestamp ASC',
                   (date, scientific_name,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# The best detections for each unique species for a given day
@detections_blueprint.route('/api/detections/date/<string:date>/highest_confidence', methods=['GET'])
def get_detections_with_highest_confidence(date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM detections WHERE id IN (SELECT id FROM detections WHERE DATE(timestamp) = ? GROUP BY scientific_name HAVING MAX(confidence))',
        (date,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# all detections for a date range
@detections_blueprint.route('/api/detections/date_range/<string:start_date>/<string:end_date>', methods=['GET'])
def get_detections_by_date_range(start_date, end_date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM detections WHERE DATE(timestamp) BETWEEN ? AND ? ORDER BY timestamp ASC',
                   (start_date, end_date,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# number of detections for a date range
@detections_blueprint.route('/api/detections/date_range/<string:start_date>/<string:end_date>/count', methods=['GET'])
def get_detection_count_by_date_range(start_date, end_date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM detections WHERE DATE(timestamp) BETWEEN ? AND ?', (start_date, end_date,))
    count = cursor.fetchone()[0]

    connection.close()

    return jsonify({"count": count})


# number of detections for a given date range for unique scientific_names, descending or ascending:
@detections_blueprint.route(
    '/api/detections/date_range/<string:start_date>/<string:end_date>/grouped/<string:sort_order>', methods=['GET'])
def get_grouped_detections_by_date_range(start_date, end_date, sort_order):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    if sort_order not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort order"}), 400

    cursor.execute(
        f'SELECT scientific_name, COUNT(*) as count FROM detections WHERE DATE(timestamp) BETWEEN ? AND ? GROUP BY scientific_name ORDER BY count {sort_order.upper()}',
        (start_date, end_date,))
    grouped_detections = cursor.fetchall()

    connection.close()

    return jsonify(grouped_detections)


# All detections for a given date range for a given scientific_name, sorted by confidence descending:
@detections_blueprint.route(
    '/api/detections/date_range/<string:start_date>/<string:end_date>/scientific_name/<string:scientific_name>/confidence',
    methods=['GET'])
def get_detections_by_scientific_name_and_confidence_date_range(start_date, end_date, scientific_name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM detections WHERE DATE(timestamp) BETWEEN ? AND ? AND scientific_name = ? ORDER BY confidence DESC',
        (start_date, end_date, scientific_name,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# All detections for a given date range for a given scientific_name, sorted by timestamp ascending:
@detections_blueprint.route(
    '/api/detections/date_range/<string:start_date>/<string:end_date>/scientific_name/<string:scientific_name>/timestamp',
    methods=['GET'])
def get_detections_by_scientific_name_and_timestamp_date_range(start_date, end_date, scientific_name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM detections WHERE DATE(timestamp) BETWEEN ? AND ? AND scientific_name = ? ORDER BY timestamp ASC',
        (start_date, end_date, scientific_name,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


# The detections for a given date range with the highest confidence for each unique scientific_name:
@detections_blueprint.route('/api/detections/date_range/<string:start_date>/<string:end_date>/highest_confidence',
                            methods=['GET'])
def get_detections_with_highest_confidence_date_range(start_date, end_date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM detections WHERE id IN (SELECT id FROM detections WHERE DATE(timestamp) BETWEEN ? AND ? GROUP BY scientific_name HAVING MAX(confidence))',
        (start_date, end_date,))
    detections = cursor.fetchall()

    connection.close()

    return jsonify(detections)


@detections_blueprint.route('/api/detections/count_by_hour/<string:date>', methods=['GET'])
def get_detections_by_day_and_hour(date):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""    
        SELECT common_name,    
               strftime('%Y-%m-%d', timestamp) AS date,    
               strftime('%H', timestamp) AS hour,    
               COUNT(*) AS count    
        FROM detections    
        WHERE date(timestamp) = date(?)    
        GROUP BY common_name, date, hour    
        ORDER BY count DESC, common_name, hour    
    """, (date,))

    data = cursor.fetchall()
    print("here's data in count_by_hour:")
    print(data, flush=True)

    # Convert the tuples to dictionaries
    results = [
        {
            'common_name': row[0],
            'date': row[1],
            'hour': row[2],
            'count': row[3],
        } for row in data
    ]

    return jsonify(results)


@detections_blueprint.route('/api/detections/by_hour/<date>/<int:hour>')
def get_detections_by_hour(date, hour):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''  
        SELECT * FROM detections  
        WHERE strftime('%Y-%m-%dT%H', timestamp) = ? || 'T' || ?  
        ORDER BY timestamp ASC  
    ''', (date, hour))

    results = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    detections = [dict(zip(column_names, result)) for result in results]

    connection.close()

    return jsonify(detections)


@detections_blueprint.route('/api/detections/by_common_name/<date>/<common_name>')
def get_detections_by_common_name(date, common_name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''    
        SELECT * FROM detections    
        WHERE strftime('%Y-%m-%d', timestamp) = ? AND common_name = ?    
        ORDER BY timestamp ASC    
    ''', (date, common_name))

    results = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    detections = [dict(zip(column_names, result)) for result in results]

    connection.close()

    return jsonify(detections)