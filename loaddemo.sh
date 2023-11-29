#!/bin/bash
set -e

source .env
source /etc/os-release

PYTHON_VERSION=${PYTHON_VERSION:-3}
POETRY=${POETRY:=false}

if $POETRY ; then
	echo "Using poetry"
	if ! test -f pyproject.toml; then
		echo "No pyproject.toml found. Please run this script from the root of the project"
		exit 1
	fi
	if ! [ -x "$(command -v poetry)" ]
	then
		echo "poetry could not be found. Please install poetry: https://python-poetry.org/docs/#installation"
		exit 1
	else
		poetry install
		poetry shell
	fi
else
	echo "Using pip"
	if ! [ -x "$(command -v pip${PYTHON_VERSION})" ]
	then
		echo "pip${PYTHON_VERSION} could not be found. Please install pip${PYTHON_VERSION}"
		exit 1
	else
		python${PYTHON_VERSION}  -mvenv venv
		. venv/bin/activate
		if [ $VERSION_ID == "23.04" -o  $VERSION_ID == "23.10" ]; then
			sudo apt install --upgrade python3-pip -y
		else
			pip${PYTHON_VERSION} install --upgrade pip
		fi
		pip${PYTHON_VERSION} install -r requirements.txt
	fi
fi

test -f db.sqlite3 && rm -f db.sqlite3

python${PYTHON_VERSION} manage.py makemigrations
python${PYTHON_VERSION} manage.py migrate
export LC_ALL=en_US.UTF-8

echo
echo Importing data
echo

if test -f demo/example.json; then
	python${PYTHON_VERSION} manage.py loaddata demo/example.json
else
	python${PYTHON_VERSION} manage.py import-wifi demo/wifi.csv
	python${PYTHON_VERSION} manage.py import-machines demo/mac.csv
	python${PYTHON_VERSION} manage.py import-consolidated demo/consolidated.txt
	python${PYTHON_VERSION} manage.py pettycash-recache
    python${PYTHON_VERSION} manage.py pettycash-activate-all-users
    echo
	echo No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:
	grep @  demo/consolidated.txt
fi

python${PYTHON_VERSION} manage.py runserver
