#!/bin/sh
set -e
DIR=${DIR:-/usr/local/makerspaceleiden-crm}
cd $DIR || exit 1

. ./venv/bin/activate

python manage.py pettycash-recache
