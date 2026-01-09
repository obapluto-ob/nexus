from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(
    'email_tool',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.collect_emails': {'queue': 'collection'},
        'tasks.verify_emails': {'queue': 'verification'},
        'tasks.send_campaign': {'queue': 'sending'},
    }
)