from app import create_app
from config import CONCURRENCY

print("Starting celery worker in celery_worker.py", flush=True)
app = create_app(init_celery=True)
celery = app.celery

if __name__ == '__main__':

    # celery.worker_main(['worker', '--loglevel=info'])
    celery.worker_main(['worker', '--loglevel=info', '--concurrency=' + str(CONCURRENCY)])

