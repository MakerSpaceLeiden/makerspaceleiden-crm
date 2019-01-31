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

# Prepare and set up the environment.
#
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# Create a super user - inital admin to be able to 
# log in.
python manage.py createsuperuser

# And start the server.
#
python manage.py runserver 

