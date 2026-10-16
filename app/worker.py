"""Expose the Celery application for the worker command.

Celery imports this object to discover the configuration and registered tasks.
The task implementation itself is in app/tasks.py.
"""
from app.tasks import celery_app

__all__ = ("celery_app",)
