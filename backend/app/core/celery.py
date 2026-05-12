import os
from celery import Celery
from celery.schedules import crontab

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

broker_url = f"redis://{redis_host}:{redis_port}/0"
result_backend = f"redis://{redis_host}:{redis_port}/0"

celery_app = Celery(
    "agentkobi",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.briefing_task"]
)

celery_app.conf.update(
    timezone="Europe/Istanbul",
    enable_utc=True,
)

# Her sabah 08:00'de brifing üret ve gönder
celery_app.conf.beat_schedule = {
    "send-morning-briefing": {
        "task": "app.tasks.briefing_task.send_morning_briefing_task",
        "schedule": crontab(hour=8, minute=0),
    },
}
