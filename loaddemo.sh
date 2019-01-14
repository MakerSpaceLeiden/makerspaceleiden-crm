#!/bin/sh
set -e
VERSION=3.7

python${VERSION}  -mvenv venv
. venv/bin/activate

pip${VERSION} install -r requirements.txt 

test db.sqlite3 && rm db.sqlite3

python${VERSION} manage.py makemigrations
python${VERSION} manage.py migrate

if test -f demo/example.json; then
	python${VERSION} manage.py loaddata demo/example.json
else
	python${VERSION} manage.py import-wifi < demo/wifi.csv
	python${VERSION} manage.py import-machines < demo/mac.csv 
	python${VERSION} manage.py import-consolidated < demo/consolidated.txt 
fi

python${VERSION} manage.py runserver
