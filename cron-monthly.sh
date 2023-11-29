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

python manage.py pettycash-recache $*
python manage.py pettycash-sent-reminders $*
python manage.py pettycash-sent-balances $*
python manage.py pettycash-consolidate $* 30
