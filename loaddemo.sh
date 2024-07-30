#!/bin/bash
set -e

test -f .env && source .env
test -f /etc/os-release && source /etc/os-release

PYTHON_VERSION=${PYTHON_VERSION:-3}
POETRY=${POETRY:=false}

unset POETRY_RUN

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
		export POETRY_RUN="poetry run "
	fi
else
	echo "Using pip"
	if ! [ -x "$(command -v pip${PYTHON_VERSION})" ]
	then
		echo "pip${PYTHON_VERSION} could not be found. Please install pip${PYTHON_VERSION}"
		exit 1
	else
		python${PYTHON_VERSION}  -m venv venv
		. venv/bin/activate
		if [ x$VERSION_ID == "x23.04" -o  x$VERSION_ID == "23.10" ]; then
			sudo apt install --upgrade python3-pip -y
		else
			pip${PYTHON_VERSION} install --upgrade pip
		fi
		pip${PYTHON_VERSION} install -r requirements.txt
	fi
fi

test -f db.sqlite3 && rm -f db.sqlite3

${POETRY_RUN}python${PYTHON_VERSION} manage.py makemigrations
${POETRY_RUN}python${PYTHON_VERSION} manage.py migrate
export LC_ALL=en_US.UTF-8

echo
echo Importing data
echo

if test -f demo/example.json; then
	${POETRY_RUN}python${PYTHON_VERSION} manage.py loaddata demo/example.json
else
        ${POETRY_RUN}python${PYTHON_VERSION} manage.py user-init
	${POETRY_RUN}python${PYTHON_VERSION} manage.py import-wifi demo/wifi.csv
	${POETRY_RUN}python${PYTHON_VERSION} manage.py import-machines demo/mac.csv
	${POETRY_RUN}python${PYTHON_VERSION} manage.py import-consolidated demo/consolidated.txt
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-import-pricelist demo/pricelist.csv
	echo -n Balance prior to loading:
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-balance-check
	echo
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-demo-gendata
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-recache
	echo -n Balance post loading:
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-balance-check
	echo
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-recache
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-balance-check
        ${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-activate-all-users
	${POETRY_RUN}python${PYTHON_VERSION} manage.py pettycash-balance-check
         echo
	echo No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:
	grep @  demo/consolidated.txt
fi

${POETRY_RUN}python${PYTHON_VERSION} manage.py runserver
