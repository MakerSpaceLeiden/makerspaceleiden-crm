#!/bin/bash
set -e

test -f .env && source .env
test -f /etc/os-release && source /etc/os-release

echo "Using uv"
if ! test -f pyproject.toml; then
	echo "No pyproject.toml found. Please run this script from the root of the project"
	exit 1
fi
if ! [ -x "$(command -v uv)" ]
then
	echo "uv could not be found. Please install uv: https://docs.astral.sh/uv/#installation" 
	exit 1
fi

DJANGO_RUN="uv run python manage.py"

test -f db.sqlite3 && rm -f db.sqlite3

${DJANGO_RUN} makemigrations
${DJANGO_RUN} migrate
export LC_ALL=en_US.UTF-8

echo
echo Importing data
echo

if test -f demo/example.json; then
	${DJANGO_RUN} loaddata demo/example.json
else
  ${DJANGO_RUN} user-init
	${DJANGO_RUN} import-wifi demo/wifi.csv
	${DJANGO_RUN} import-machines demo/mac.csv
	${DJANGO_RUN} import-consolidated demo/consolidated.txt
	${DJANGO_RUN} pettycash-import-pricelist demo/pricelist.csv
	${DJANGO_RUN} pettycash-balance-check
	${DJANGO_RUN} pettycash-demo-gendata
	${DJANGO_RUN} pettycash-recache
	${DJANGO_RUN} pettycash-balance-check
	${DJANGO_RUN} pettycash-recache
	${DJANGO_RUN} pettycash-balance-check
  ${DJANGO_RUN} pettycash-activate-all-users
	${DJANGO_RUN} pettycash-balance-check
  echo
	echo No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:
	grep @  demo/consolidated.txt
fi

${DJANGO_RUN} runserver
