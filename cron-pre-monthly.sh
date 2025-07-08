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

${DJANGO_RUN} memberlist-sent-list
