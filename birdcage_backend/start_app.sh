#!/bin/bash

#
# Gunicorn won't pass environment variables by default,
# so pass anything we might be specifying in docker-compose.
#
# SCRIPT_NAME is a wsgi convenience feature that gunicorn
# uses to tell Flask that the application may live in a subfolder.
#

# Start the Flask app using gunicorn
echo "Starting API Server"
gunicorn --bind 0.0.0.0:${API_SERVER_PORT} \
	-e ANALYZE_PORT="${ANALYZE_PORT}" \
	-e ANALYZE_SERVER="${ANALYZE_SERVER}" \
	-e CONCURRENCY="${CONCURRENCY}" \
	-e CORS_ORIGINS="${CORS_ORIGINS}" \
	-e DATABASE_FILE="${DATABASE_FILE}" \
	-e DETECTION_DIR_NAME="${DETECTION_DIR_NAME}" \
	-e JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
	-e REDIS_PORT="${REDIS_PORT}" \
	-e REDIS_SERVER="${REDIS_SERVER}" \
	-e SCRIPT_NAME="${SCRIPT_NAME}" \
	-e TEMP_DIR_NAME="${TEMP_DIR_NAME}" \
        run:app > >(cat >&1) 2> >(cat >&2) &

echo "Starting celery_worker"
# Start the Celery worker
python celery_worker.py > >(cat >&1) 2> >(cat >&2) &

echo "Sleeping indefinitely"
# Sleep indefinitely
while true; do sleep 1000; done
