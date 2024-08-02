#!/bin/sh
#
# Requirements
# gitt
# Python 3.7
# Python 3 venv
#
# e.g. apt install python3.7 python3.7-venv git

# Recent copy of the code:
#
git clone https://github.com/dirkx/makerspaceleiden-crm.git

# Setup virtual environment as conveniet.
#
cd makerspaceleiden-crm/
python3.7 -m venv venv
 . venv/bin/activate

# Install dependencies - default test install asume SQLLite as
# the db.
#
# OSX 10.14 users with a locked down ~/Library; use
# pip install --no-cache-dir -r requirements.txt
# to avoid having to write in ~/Library/Caches/pip/wheel..
#
pip install -r requirements.txt

# Uncomment to also include mysql and other production requirements.
#
# pip install -r requirements-production.txt

# Prepare and set up the environment.
#
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# Create a super user - inital admin to be able to
# log in.
python manage.py createsuperuser

# Next create some special role users for payments
# and a 'none' user that acts as a garbage collector for
# users who have left (i.e. owns thier boxes/money, etc)
#
# You do not have to create these here. It is also
# possible to change the NONE_ID and POT_IDs in settings
# to point to some manually created user.
#
python manage.py user-init.

# And start the server.
#
python manage.py runserver

# or add --settings=makerspaceleiden.local_with_db to run on mysql locally
