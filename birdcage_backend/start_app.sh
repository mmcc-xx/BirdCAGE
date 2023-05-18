#!/bin/bash

# Start the Flask app using gunicorn
echo "Starting API Server"
gunicorn --bind 0.0.0.0:$API_SERVER_PORT run:app > >(cat >&1) 2> >(cat >&2) &

echo "Starting celery_worker"
# Start the Celery worker
python celery_worker.py > >(cat >&1) 2> >(cat >&2) &

echo "Sleeping indefinitely"
# Sleep indefinitely
while true; do sleep 1000; done
