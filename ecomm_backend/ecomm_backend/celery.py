import os
from pathlib import Path

from celery import Celery

# Load .env before Django settings (so GMAIL_* vars are available)
try:
    from dotenv import load_dotenv
    base = Path(__file__).resolve().parent.parent  # ecomm_backend/
    load_dotenv(base / ".env") or load_dotenv(base.parent / ".env")  # backend/
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomm_backend.settings")

app = Celery("ecomm_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
