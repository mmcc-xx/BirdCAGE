# Use the official Python 3.10 image as the base image
FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt /
# Install Python packages from requirements.txt
RUN pip install -r requirements.txt

# Install Gunicorn
RUN pip install gunicorn

# Copy files into the container
COPY run.py start_app.sh config.py celery_worker.py /
COPY app /app

# Set environment variables
ENV DATABASE_FILE=/db/birdcage.db \
    API_SERVER_PORT=7007 \
    TEMP_DIR_NAME=tmp \
    ANALYZE_SERVER=192.168.1.75 \
    ANALYZE_PORT=7667 \
    DETECTION_DIR_NAME=detections \
    CORS_ORIGINS=http://192.168.1.75:7008 \
    REDIS_SERVER=192.168.1.75 \
    REDIS_PORT=6379

# Grant execution permission to start_app.sh
RUN chmod +x start_app.sh

# Start the app
CMD ["./start_app.sh"]
