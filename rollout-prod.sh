#!/bin/bash
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

# Set uv environment variables to use the system-wide cache and install directory
# the default behaviour is to use the user's home directory for these.
export UV_CACHE_DIR=/usr/local/.uv
export UV_PYTHON_INSTALL_DIR=/usr/local/.uv

# Validate that directories exist and are writable
check_dir() {
    local dir="$1"
    local name="$2"
    if [ ! -d "$dir" ]; then
        echo "ERROR: $name does not exist: $dir"
        exit 1
    fi
    if [ ! -w "$dir" ]; then
        echo "ERROR: $name is not writable: $dir"
        exit 1
    fi
}

check_dir "$UV_CACHE_DIR" "UV_CACHE_DIR"
check_dir "$UV_PYTHON_INSTALL_DIR" "UV_PYTHON_INSTALL_DIR"

echo "Using UV_CACHE_DIR: $UV_CACHE_DIR"
echo "Using UV_PYTHON_INSTALL_DIR: $UV_PYTHON_INSTALL_DIR"

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
sudo chmod 000 /tmp/backup-static.$UK /tmp/backup.$UK
sudo chown root /tmp/backup-static.$UK /tmp/backup.$UK


${DJANGO_RUN} collectstatic --no-input
${DJANGO_RUN} makemigrations
${DJANGO_RUN} migrate

sudo apachectl restart
sudo systemctl restart crm-daphne.service
)
E=$?

cleanup
exit $E
