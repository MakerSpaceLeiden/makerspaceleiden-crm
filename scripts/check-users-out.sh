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
users = list(User.objects.filter(is_onsite=True))
for user in users:
    try:
        user.checkout()
        print(f'✓ Checked out {user.email}')
    except Exception as e:
        print(f'✗ Failed to check in {user.email}: {e}')
EOF
