#!/bin/sh
set -e
DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

. ./venv/bin/activate

python manage.py pettycash-recache
python manage.py pettycash-sent-reminders
python manage.py pettycash-sent-balances 
python manage.py pettycash-consolidate 30
