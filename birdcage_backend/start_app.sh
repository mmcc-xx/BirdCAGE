#!/bin/bash

# Start the Flask app using gunicorn
gunicorn --bind 0.0.0.0:$SERVER_PORT run:app

# Start the Celery worker
# python celery_worker.py &
