# Get current git SHA
SHA=$(git rev-parse HEAD)

# Create .env if it doesn't exist
touch .env

# Update or add SITE_VERSION
if grep -q "^SITE_VERSION=" .env; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^SITE_VERSION=.*/SITE_VERSION=$SHA/" .env
    else
        sed -i "s/^SITE_VERSION=.*/SITE_VERSION=$SHA/" .env
    fi
else
    # Add new line
    echo "SITE_VERSION=$SHA" >> .env
fi
