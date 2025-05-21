#!/bin/sh
UK=$$
DAYS=30

trap cleanup INT
cleanup () {
	if test -f /tmp/backup.$UK; then
	       	echo "Warning - the files /tmp/*.$UK will be deleted in ${DAYS} days."
		echo "          Or you can do it earlier yourself."
		echo
		at now + ${DAYS} days <<EOM
rm -f /tmp/backup.$UK /tmp/backup-static.$UK
EOM
	fi
}

uv venv
source .venv/bin/activate

DJANGO_RUN="uv run python manage.py"

if !  ${DJANGO_RUN} version > /dev/null; then
	echo Check with manage.py first - some compile errors.
	exit 1
fi

(
set -e

test -e makerspaceleiden/settings.py
test -e makerspaceleiden/local.py

sudo chgrp -R crmadmin .
sudo chmod -R g+rw .

uv sync

# Outputs all data in the database associated with installed applications
${DJANGO_RUN} dumpdata | gzip -c > /tmp/backup.$UK
test -d static && tar zcf /tmp/backup-static.$UK static

# Mickey-mouse lock - we should pub-key encrypt this.
#
cmod 000 /tmp/backup-static.$UK /tmp/backup.$UK
chown root /tmp/backup-static.$UK /tmp/backup.$UK


${DJANGO_RUN} collectstatic --no-input
${DJANGO_RUN} makemigrations
${DJANGO_RUN} migrate

sudo apachectl restart
sudo systemctl restart crm-daphne.service
)
E=$?

cleanup
exit $E
