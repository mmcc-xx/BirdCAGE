from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from celery import Celery
from celery.schedules import crontab
from .celery_config import broker_url, result_backend
from .stream_processing import process_streams
from app.views.streams import streams_blueprint
from app.views.preferences import preferences_blueprint
from app.views.audio_files import audio_files_blueprint
from app.views.detections import detections_blueprint
from app.views.filters import filters_blueprint
from app.views.notifications import notifications_blueprint
from app.views.commands import commands_blueprint
from app.views.app_health import app_heath_blueprint
from app.models.streams import create_streams_table
from app.models.preferences import create_preferences_table
from app.models.recording_metadata import create_recording_metadata_table
from app.models.detections import create_detections_table
from app.models.filters import create_filters_tables
from app.models.notifications import create_notification_services_table, create_notification_assignments_table
from app.models.commands import create_commands_table
from config import CORS_ORIGINS, JWT_SECRET_KEY


def create_app(init_celery=True):
    app = Flask(__name__, static_url_path='/static', static_folder='static')

    cors_origins = CORS_ORIGINS.split(',')
    CORS(app, origins=cors_origins)

    create_streams_table()
    create_preferences_table()
    create_recording_metadata_table()
    create_detections_table()
    create_filters_tables()
    create_notification_services_table()
    create_notification_assignments_table()
    create_commands_table()

    if init_celery:
        # Initialize Celery
        app.config['CELERY_BROKER_URL'] = broker_url
        app.config['RESULT_BACKEND'] = result_backend
        # print("Broker URL: " + app.config['CELERY_BROKER_URL'])
        # print("Result Backend: " + app.config['RESULT_BACKEND'])
        app.celery = make_celery(app)

        # start recording and processing streams
        process_streams()

    else:
        # Register blueprint

        app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY  # Replace with your own secret key

        jwt = JWTManager(app)

        app.register_blueprint(streams_blueprint)
        app.register_blueprint(preferences_blueprint)
        app.register_blueprint(audio_files_blueprint)
        app.register_blueprint(detections_blueprint)
        app.register_blueprint(filters_blueprint)
        app.register_blueprint(notifications_blueprint)
        app.register_blueprint(commands_blueprint)
        app.register_blueprint(app_heath_blueprint)

    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery
