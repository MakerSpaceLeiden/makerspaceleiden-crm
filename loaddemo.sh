#!/bin/sh
set -e
VERSION=${VERSION:-3.7}

python${VERSION}  -mvenv venv
. venv/bin/activate

pip${VERSION} install -r requirements.txt 

test -f db.sqlite3 && rm -f db.sqlite3

python${VERSION} manage.py makemigrations
python${VERSION} manage.py migrate

echo
echo Importing data
echo 

if test -f demo/example.json; then
	python${VERSION} manage.py loaddata demo/example.json
else
	python${VERSION} manage.py import-wifi < demo/wifi.csv
	python${VERSION} manage.py import-machines < demo/mac.csv 
	python${VERSION} manage.py import-consolidated < demo/consolidated.txt 
	echo " Reset all password and generate invites (Y, N) ?"
	read I
	if [ "x$I" = "xY" ]; then
		python${VERSION} manage.py sent-invite --reset --all
	else
		echo Passwords are all set to 1234 for:
		grep @  demo/consolidated.txt
	fi
fi

python${VERSION} manage.py runserver
