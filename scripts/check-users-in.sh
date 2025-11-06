#!/bin/bash

# Check in a random set of users using Django manage.py
# Usage: ./scripts/check-users-in.sh [num_users] [location_id]

set -e

NUM_USERS=${1:-5}  # Default to 5 users if not specified
LOCATION_ID=${2:-}  # Optional location_id

uv run manage.py shell <<EOF
import sys
from members.models import User
from acl.models import Location

# Get random active users
users = list(User.objects.filter(is_active=True).order_by('?')[:${NUM_USERS}])
location = None

location_id = '${LOCATION_ID}'
if location_id:
    try:
        location = Location.objects.get(pk=int(location_id))
    except Location.DoesNotExist:
        print(f'Location with id {location_id} not found')
        sys.exit(1)
    except ValueError:
        print(f'Invalid location_id: {location_id}')
        sys.exit(1)

if not users:
    print('No active users found')
    sys.exit(1)

print(f'Checking in {len(users)} random users...')
for user in users:
    try:
        user.checkin(location=location)
        location_str = f' at {location.name}' if location else ''
        print(f'✓ Checked in {user.email}{location_str}')
    except Exception as e:
        print(f'✗ Failed to check in {user.email}: {e}')
EOF
