#!/bin/sh
set -e

TMPDIR=${TMPDIR:-/tmp}
cd $TMPDIR

NAME=${NAME:-foo}
TAG=${TAG:-1-2-3}
MACHINE=${MACHINE:-Bandsaw}
NODE=${NODE:-foo}
MACHINEID=${MACHINEID:-1}
BEARERSECRET=Foo

if ! test -f x-client-$NAME.pem; then
	echo "Run the test in terminal first; with $NAME as its argument.\n\
		This creates the credentials, etc."
        exit 1
fi

set `openssl x509 -outform DER -in x-client-$NAME.pem | openssl sha256`
CLIENT_SHA=$2
set `openssl x509 -outform DER -in x-server.pem | openssl sha256`
SERVER_SHA=$2

CLIENT_PEM=$(cat x-client-$NAME.pem | tr -s '\n' ' ')
SERVER_PEM=$(cat x-server.pem | tr -s '\n' ' ')

echo Checkig if the user can pay for something
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}" \
	-H "X-Bearer: ${BEARERSECRET}" \
	-d node=${NAME} \
        -d src=${TAG} \
        -d amount=1.00 \
        -d description="25 grammes of red PLA (old API, node ${NAME})" \
	http://127.0.0.1:8000/pettycash/api/v1/pay | jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d src=${TAG} \
        -d amount=1.00 \
        -d description="25 grammes of red PLA (new API, node ${NAME})" \
	http://127.0.0.1:8000/pettycash/api/v2/pay | jq
