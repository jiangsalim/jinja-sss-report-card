#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py makemigrations accounts academic students teachers grading
python manage.py makemigrations
python manage.py migrate

echo "Seeding system data..."
python manage.py seed_system

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build complete!"
