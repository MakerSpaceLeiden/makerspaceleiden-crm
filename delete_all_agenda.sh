#!/bin/bash

# This script deletes all Agenda objects from the database

uv run manage.py shell <<EOF
from agenda.models import Agenda
Agenda.objects.all().delete()
EOF

echo "All Agenda objects have been deleted." 