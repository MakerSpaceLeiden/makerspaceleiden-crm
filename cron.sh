#!/bin/sh
set -e
cd /usr/local/makerspaceleiden-crm
. ./venv/bin/activate

python manage.py pettycash-recache
python manage.py sent-pettycash-reminders
python manage.py sent-pettycash-balances --direct
python manage.py sent-pettycash-consolidate 30
