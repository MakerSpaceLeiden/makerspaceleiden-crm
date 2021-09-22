#!/bin/sh
set -e
VERSION=${VERSION:-3}

export LC_ALL=en_US.UTF-8

python${VERSION}  -mvenv venv
. venv/bin/activate

python${VERSION} manage.py makemigrations
python${VERSION} manage.py migrate
python${VERSION} manage.py runserver
