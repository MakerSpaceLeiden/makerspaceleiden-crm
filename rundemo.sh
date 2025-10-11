#!/bin/sh
set -e
test -f .env && source .env

if ! [ -x "$(command -v uv)" ]
then
	echo "uv could not be found. Please install uv: https://docs.astral.sh/uv/#installation"
	exit 1
fi


DJANGO_RUN="uv run python manage.py"

${DJANGO_RUN} makemigrations
${DJANGO_RUN} migrate
${DJANGO_RUN} runserver 7000
