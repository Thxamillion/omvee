from celery import Celery
from app.config import settings

celery_app = Celery(
    "omvee",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'app.workers.tasks.*': {'queue': 'default'},
    }
)