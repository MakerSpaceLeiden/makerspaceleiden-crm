#!/bin/bash

set -e

test -f .env && source .env

DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

uv venv --allow-existing
source .venv/bin/activate

DJANGO_RUN="uv run python manage.py"

if !  ${DJANGO_RUN} version > /dev/null; then
	echo Check with manage.py first - some compile errors.
	exit 1
fi

${DJANGO_RUN} pettycash-recache $*
${DJANGO_RUN} pettycash-sent-reminders $*
${DJANGO_RUN} pettycash-sent-balances $*
${DJANGO_RUN} pettycash-sent-sku-monthly-count $*
${DJANGO_RUN} pettycash-consolidate 30 $*
