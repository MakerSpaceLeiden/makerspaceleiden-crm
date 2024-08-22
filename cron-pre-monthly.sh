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

${POETRY_RUN}python manage.py  memberlist-sent-list
