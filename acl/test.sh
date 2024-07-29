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

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "X-Bearer: ${BEARERSECRET}" \
        -d tag=${TAG} http://127.0.0.1:8000/acl/api/v1/getok/${MACHINE} | jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "X-Bearer: ${BEARERSECRET}" \
        -d tag=${TAG} \
	http://127.0.0.1:8000/acl/api/v1/getok4node/${NODE}| jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "X-Bearer: ${BEARERSECRET}" \
        -d tag=${TAG} \
	http://127.0.0.1:8000/acl/api/v1/gettaginfo | jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "X-Bearer: ${BEARERSECRET}" \
        http://127.0.0.1:8000/acl/$MACHINEID

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
	http://127.0.0.1:8000/acl/api/v1/gettags4node/${NODE}| jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
	http://127.0.0.1:8000/acl/api/v1/gettags4machine/${MACHINE} | jq
