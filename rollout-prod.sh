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
rm -rf /tmp/*.$UK
EOM
	fi
}

(
test -d makerspaceleiden/settings.py

set -e
sudo chgrp -R crmadmin .
sudo chmod -R g+rw .

. ./venv/bin/activate

pip install -r requirements.txt  --quiet

python manage.py dumpdata | gzip -c > /tmp/backup.$UK
test -d static && tar zcf /tmp/backup-static.$UK static

python manage.py collectstatic --no-input

python manage.py makemigrations
python manage.py migrate

sudo apachectl restart
)
E=$?

cleanup
exit $E
