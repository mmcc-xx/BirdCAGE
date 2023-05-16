from app import create_app

app = create_app(init_celery=True)
celery = app.celery

if __name__ == '__main__':
    celery.worker_main(['worker', '--loglevel=info'])
