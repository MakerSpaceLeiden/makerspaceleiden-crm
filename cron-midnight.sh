#!/bin/bash

set -e

source .env

DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

POETRY=${POETRY:=false}

if $POETRY ; then
    poetry shell
else
    . ./venv/bin/activate
fi

python manage.py pettycash-recache
python manage.py clean_duplicate_history --auto > /dev/null
python manage.py clean_old_history --days 1000 --auto > /dev/null
python manage.py sent-ufo-reminders
