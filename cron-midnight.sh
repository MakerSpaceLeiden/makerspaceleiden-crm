#!/bin/bash

set -e

test -f .env && source .env

DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

uv venv --allow-existing --quiet
source .venv/bin/activate

DJANGO_RUN="uv run python manage.py"

if !  ${DJANGO_RUN} version > /dev/null; then
	echo Check with manage.py first - some compile errors.
	exit 1
fi

{
	date
	${DJANGO_RUN} pettycash-balance-check
	${DJANGO_RUN} pettycash-transactions --days 1
} >> /tmp/balance-debugging-dirkx.txt

${DJANGO_RUN} pettycash-recache
${DJANGO_RUN} clean_duplicate_history --auto > /dev/null
${DJANGO_RUN} clean_old_history --days 1000 --auto > /dev/null
${DJANGO_RUN} send-acl-reminders > /dev/null
${DJANGO_RUN} generate_events --limit=90 > /dev/null
