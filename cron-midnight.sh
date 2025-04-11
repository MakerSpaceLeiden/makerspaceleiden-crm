#!/bin/bash

set -e

test -f .env && source .env

DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

POETRY=${POETRY:=false}

unset POETRY_RUN

if $POETRY ; then
    export POETRY_RUN="poetry run "
else
    . ./venv/bin/activate
fi

${POETRY_RUN}python manage.py pettycash-recache
${POETRY_RUN}python manage.py clean_duplicate_history --auto > /dev/null
${POETRY_RUN}python manage.py clean_old_history --days 1000 --auto > /dev/null
${POETRY_RUN}python manage.py send-acl-reminders > /dev/null
