#!/bin/sh
set -e

python3.7 -mvenv venv
. venv/bin/activate

pip3.7 install -r requirements.txt 

test db.sqlite3 && rm db.sqlite3

python3.7 manage.py makemigrations
python3.7 manage.py migrate

if test -f demo/example.json; then
	python3.7 manage.py loaddata demo/example.json
else
	python3.7 manage.py import-wifi < demo/wifi.csv
	python3.7 manage.py import-machines < demo/mac.csv 
	python3.7 manage.py import-consolidated < demo/consolidated.txt 
fi

python3.7 manage.py runserver
