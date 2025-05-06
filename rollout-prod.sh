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

. ./venv/bin/activate
if !  python manage.py version > /dev/null; then
	echo Check with manage.py first - some compile errors.
	exit 1
fi

(
set -e

test -e makerspaceleiden/settings.py
test -e makerspaceleiden/local.py

sudo chgrp -R crmadmin .
sudo chmod -R g+rw .

. ./venv/bin/activate

pip install --upgrade pip --quiet
pip install -r requirements.txt  --quiet

python manage.py dumpdata | gzip -c > /tmp/backup.$UK
test -d static && tar zcf /tmp/backup-static.$UK static

# Mickey-mouse lock - we should pub-key encrypt this.
#
sudo chmod 000 /tmp/backup-static.$UK /tmp/backup.$UK
sudo chown root /tmp/backup-static.$UK /tmp/backup.$UK

python manage.py collectstatic --no-input

python manage.py makemigrations
python manage.py migrate

sudo apachectl restart
sudo systemctl restart crm-daphne.service
)
E=$?

cleanup
exit $E
