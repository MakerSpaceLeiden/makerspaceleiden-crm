#!/bin/sh
set -e
VERSION=${VERSION:-3}

python${VERSION}  -mvenv venv
. venv/bin/activate

pip install --upgrade pip
pip${VERSION} install -r requirements.txt 

test -f db.sqlite3 && rm -f db.sqlite3

python${VERSION} manage.py makemigrations
python${VERSION} manage.py migrate
 export LC_ALL=en_US.UTF-8

echo
echo Importing data
echo 

if test -f demo/example.json; then
	python${VERSION} manage.py loaddata demo/example.json
else
	python${VERSION} manage.py import-wifi demo/wifi.csv
	python${VERSION} manage.py import-machines demo/mac.csv 
	python${VERSION} manage.py import-consolidated demo/consolidated.txt 
	python${VERSION} manage.py pettycash-recache
	echo " Reset all password and generate invites (Y, N, default is No) ?"
	read I
	if [ "x$I" = "xY" ]; then
		python${VERSION} manage.py sent-invite --reset --all
	else
		echo No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:
		grep @  demo/consolidated.txt
	fi
fi

python${VERSION} manage.py runserver
