#!/bin/sh
#
# Requirements
# gitt
# Python 3.x
# Python 3 venv
# 
# e.g. apt install python3 python3-venv git

# Recent copy of the code:
#
git clone https://github.com/dirkx/makerspaceleiden-crm.git

# Setup virtual environment as conveniet.
#
cd makerspaceleiden-crm/
python3.6 -m venv .
 . bin/activate

# Install dependencies - default test install asume SQLLite as
# the db.
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

