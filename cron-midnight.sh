#!/bin/sh
set -e
DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

. ./venv/bin/activate

python manage.py pettycash-recache
python manage.py clean_duplicate_history --auto > /dev/null
python manage.py clean_old_history --days 1000 --auto > /dev/null
