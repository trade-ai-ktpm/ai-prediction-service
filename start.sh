#!/bin/sh

# Start Celery worker in background for executing tasks (if needed)
# celery -A src.celery_app worker --loglevel=info --logfile=/var/log/celery-worker.log &

# Celery Beat disabled to save API quota (enable only for production with paid tier)
# celery -A src.celery_app beat --loglevel=info --logfile=/var/log/celery-beat.log &

# Wait a moment for Celery to start
# sleep 2

# Start FastAPI with uvicorn
exec uvicorn src.main:app --host 0.0.0.0 --port ${API_PORT:-8002}
