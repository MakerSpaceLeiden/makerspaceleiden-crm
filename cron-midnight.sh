#!/bin/bash

set -e

test -f .env && source .env

DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

uv venv
source .venv/bin/activate

DJANGO_RUN="uv run python manage.py"

if !  ${DJANGO_RUN} version > /dev/null; then
	echo Check with manage.py first - some compile errors.
	exit 1
fi

${DJANGO_RUN} pettycash-recache
${DJANGO_RUN} clean_duplicate_history --auto > /dev/null
${DJANGO_RUN} clean_old_history --days 1000 --auto > /dev/null
${DJANGO_RUN} send-acl-reminders > /dev/null
