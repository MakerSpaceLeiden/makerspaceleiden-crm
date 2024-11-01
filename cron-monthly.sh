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

${POETRY_RUN}python manage.py pettycash-recache $*
${POETRY_RUN}python manage.py pettycash-sent-reminders $*
${POETRY_RUN}python manage.py pettycash-sent-balances $*
${POETRY_RUN}python manage.py pettycash-consolidate 30 $*
