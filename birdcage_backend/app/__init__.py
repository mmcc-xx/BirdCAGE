from flask import Flask
from flask_cors import CORS
from celery import Celery
from .celery_config import broker_url, result_backend
from .stream_processing import process_streams
from app.views.streams import streams_blueprint
from app.views.preferences import preferences_blueprint
from app.views.audio_files import audio_files_blueprint
from app.views.detections import detections_blueprint


def create_app(init_celery=True):
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    CORS(app, origins=[
        "http://192.168.1.75:7008",
        "http://birdcage.casefamily.audioandoddities.com"
    ])

    if init_celery:
        # Initialize Celery
        app.config['CELERY_BROKER_URL'] = broker_url
        app.config['CELERY_RESULT_BACKEND'] = result_backend
        app.celery = make_celery(app)
        # start recording and processing streams
        process_streams()

    else:
        # Register blueprint
        app.register_blueprint(streams_blueprint)
        app.register_blueprint(preferences_blueprint)
        app.register_blueprint(audio_files_blueprint)
        app.register_blueprint(detections_blueprint)

    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
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
