#!/bin/sh
set -e
source .env

VERSION=${VERSION:-3}
POETRY=${POETRY:-false}

export LC_ALL=en_US.UTF-8

unset POETRY_RUN

# python${VERSION}  -mvenv venv
# . venv/bin/activate

if $POETRY; then
    echo "Using poetry"
    if ! test -f pyproject.toml; then
        echo "No pyproject.toml found. Please run this script from the root of the project"
        exit 1
    fi
    if ! [ -x "$(command -v poetry)" ]
    then
        echo "poetry could not be found. Please install poetry: https://python-poetry.org/docs/#installation"
        exit 1
    else
        poetry install
        export POETRY_RUN="poetry run "
    fi
else
    echo "Using pip"
    if ! [ -x "$(command -v pip${VERSION})" ]
    then
        echo "pip${VERSION} could not be found. Please install pip${VERSION}"
        exit 1
    else
        . venv/bin/activate
    fi
fi

${POETRY_RUN}python${VERSION} manage.py makemigrations
${POETRY_RUN}python${VERSION} manage.py migrate
${POETRY_RUN}python${VERSION} manage.py runserver
