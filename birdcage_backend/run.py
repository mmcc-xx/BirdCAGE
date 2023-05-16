from app import create_app
from app.models.streams import create_streams_table
from app.models.preferences import create_preferences_table
from app.models.recording_metadata import create_recording_metadata_table
from app.models.detections import create_detections_table
from flask import Flask, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from config import SERVER_PORT

app = create_app(init_celery=False)

# Set up Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/static/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "My API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Redirect the root URL to Swagger UI
@app.route('/')
def index():
    return redirect('/api/docs')


if __name__ == '__main__':
    create_streams_table()
    create_preferences_table()
    create_recording_metadata_table()
    create_detections_table()
    app.run(host='0.0.0.0', port=SERVER_PORT)
