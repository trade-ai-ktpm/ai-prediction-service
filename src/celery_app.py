from celery import Celery
from src.config import settings

celery_app = Celery(
    "ai_prediction",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.tasks.prediction_task", "src.tasks.precompute_task"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    "precompute-top-coins-every-15-minutes": {
        "task": "src.tasks.precompute_task.precompute_top_coins",
        "schedule": 900.0,
    },
}
