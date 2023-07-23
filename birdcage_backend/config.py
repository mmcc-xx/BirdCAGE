import os

ANALYZE_PORT = int(os.environ.get('ANALYZE_PORT', 7667))
ANALYZE_SERVER = os.environ.get('ANALYZE_SERVER', '192.168.1.75')
API_SERVER_PORT = int(os.environ.get('API_SERVER_PORT', 7006))
CONCURRENCY = os.environ.get('CONCURRENCY', 10)
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://192.168.1.75:7009')
DATABASE_FILE = os.environ.get('DATABASE_FILE', 'birdcage.db')
DETECTION_DIR_NAME = os.environ.get('DETECTION_DIR_NAME', 'detections')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'TheseAreTheTimesThatTryMensSouls')
TEMP_DIR_NAME = os.environ.get('TEMP_DIR_NAME', 'tmp')
REDIS_SERVER = os.environ.get('REDIS_SERVER', '192.168.1.75')
REDIS_PORT = os.environ.get('REDIS_PORT', 6380)
SCRIPT_NAME = os.environ.get('SCRIPT_NAME')
