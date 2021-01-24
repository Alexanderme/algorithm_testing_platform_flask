#!/bin/bash
celery worker -A celery_worker.celery --loglevel=info &
gunicorn  manage:app -c  ./gunicorn.conf.py
