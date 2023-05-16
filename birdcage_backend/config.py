import os

DATABASE_FILE = os.environ.get('DATABASE_FILE', 'birdcage.db')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 7007))
TEMP_DIR_NAME = os.environ.get('TEMP_DIR_NAME', 'tmp')
ANALYZE_SERVER = os.environ.get('ANALYZE_SERVER', '192.168.1.75')
ANALYZE_PORT = int(os.environ.get('ANALYZE_PORT', 7667))
DETECTION_DIR_NAME = os.environ.get('DETECTION_DIR_NAME', 'detections')
