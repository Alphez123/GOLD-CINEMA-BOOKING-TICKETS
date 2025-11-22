#!/usr/bin/env bash
# exit on error
set -o errexit

# Move into backend folder
cd goldcinema_backend

# Install requirements from the root directory
pip install -r ../requirements.txt

# Django commands
python manage.py collectstatic --no-input
python manage.py migrate
