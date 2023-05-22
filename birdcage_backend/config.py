import os

DATABASE_FILE = os.environ.get('DATABASE_FILE', 'birdcage.db')
API_SERVER_PORT = int(os.environ.get('API_SERVER_PORT', 7006))
TEMP_DIR_NAME = os.environ.get('TEMP_DIR_NAME', 'tmp')
ANALYZE_SERVER = os.environ.get('ANALYZE_SERVER', '192.168.1.75')
ANALYZE_PORT = int(os.environ.get('ANALYZE_PORT', 7667))
DETECTION_DIR_NAME = os.environ.get('DETECTION_DIR_NAME', 'detections')
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://192.168.1.75:7009')
REDIS_SERVER = os.environ.get('REDIS_SERVER', '192.168.1.75')
REDIS_PORT = os.environ.get('REDIS_PORT', 6380)
