from datetime import datetime
from flask import Blueprint, jsonify
from redis import Redis
from config import REDIS_PORT, REDIS_SERVER, DATABASE_FILE
import os
import sqlite3


redis_client = Redis(host=REDIS_SERVER, port=REDIS_PORT, db=1)

app_heath_blueprint = Blueprint('app_health', __name__)


def get_value_or_default(redis_client, task_id, field, default_value):
    value = redis_client.hget(task_id, field)
    return default_value if value is None else value.decode('utf-8')


@app_heath_blueprint.route('/api/app_health/task_health')
def task_health():
    # Get all task IDs from the Redis set
    task_ids = redis_client.smembers('task_ids')

    # Get the monitor_tasks task ID from Redis
    monitor_task_id = redis_client.get('monitor_task_id')
    if monitor_task_id:
        task_ids.add(monitor_task_id)

    tasks_data = []

    # Iterate through the task IDs and access the hashes
    for task_id in task_ids:
        task_id = task_id.decode('utf-8')  # Convert bytes to string

        last_exception_timestamp = get_value_or_default(redis_client, task_id, 'last_exception_timestamp', None)

        # Convert the timestamp to a formatted date and time string
        if last_exception_timestamp is not None:
            last_exception_timestamp = float(last_exception_timestamp)
            last_exception_timestamp = datetime.fromtimestamp(last_exception_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        task_data = {
            'task_id': task_id,
            'task_name': get_value_or_default(redis_client, task_id, 'task_name', 'N/A'),
            'last_iteration_status': get_value_or_default(redis_client, task_id, 'last_iteration_status', 'N/A'),
            'consecutive_successes': int(get_value_or_default(redis_client, task_id, 'consecutive_successes', 0)),
            'consecutive_fails': int(get_value_or_default(redis_client, task_id, 'consecutive_fails', 0)),
            'last_exception': get_value_or_default(redis_client, task_id, 'last_exception', 'N/A'),
            'last_exception_timestamp': last_exception_timestamp
        }

        tasks_data.append(task_data)

        # Return the tasks data as a JSON document
    return jsonify(tasks_data)


def get_table_stats(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    table_stats = []
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        table_stats.append({"table_name": table_name, "row_count": row_count})

    return table_stats


def perform_integrity_check(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    return result == "ok"


@app_heath_blueprint.route('/api/app_health/db_health')
def db_health():
    conn = sqlite3.connect(DATABASE_FILE)

    db_stats = {
        "file_size": os.path.getsize(DATABASE_FILE),
        "table_stats": get_table_stats(conn),
        "integrity_check": perform_integrity_check(conn)
    }

    conn.close()

    return jsonify(db_stats)
