#!/bin/sh

if [ $# -gt 3 -o "x$1" = "x-h" ]; then
	echo "Syntax: $0 [name [tag [ip]]]"
	exit 1
fi

set -e
TMPDIR=${TMPDIR:-/tmp}
cd $TMPDIR

NAME=${1:-test-$$}
TAG=${2:-1-2-3}
IP=${3:-10.11.12.113}

if ! test -f x-server.pem; then
	openssl genrsa | openssl x509 -new  -subj "/CN=the server" -out x-server.pem -key /dev/stdin
fi

if test -f x-client-$NAME.pem; then
	echo existing key used
else
	openssl genrsa > x-client-$NAME.key
	openssl x509 -new  -subj "/CN=$NAME/O=terminal" -out x-client-$NAME.pem -key x-client-$NAME.key
	cat x-client-$NAME.key x-client-$NAME.pem > x-client-$NAME.crt
fi

set `openssl x509 -outform DER -in x-client-$NAME.pem | openssl sha256`
CLIENT_SHA=$2
set `openssl x509 -outform DER -in x-server.pem | openssl sha256`
SERVER_SHA=$2

CLIENT_PEM=$(cat x-client-$NAME.pem | tr -s '\n' ' ')
SERVER_PEM=$(cat x-server.pem | tr -s '\n' ' ')

DIGEST=$(
   curl --silent \
	-H "X-FORWARDED-FOR: ${IP}"  \
	-H "SSL-CLIENT-CERT: $CLIENT_PEM" \
	-H "SSL-SERVER-CERT: $SERVER_PEM" \
	--cert client-$NAME.crt \
	http://127.0.0.1:8000/terminal/api/v2/register\?name=$NAME
)
if echo $DIGEST | grep -q '{'; then
	echo Already paired ok.
	echo Pricelist: $DIGEST
	exit 0
fi

set `
(
	/bin/echo -n $DIGEST
	/bin/echo -n $TAG;
	/bin/echo $CLIENT_SHA | xxd -r -p
	/bin/echo $SERVER_SHA | xxd -r -p
) | openssl sha256
`
RESPONSE=$2

set `curl --silent \
 	-H "X-FORWARDED-FOR: ${IP}"  \
	-H "SSL-CLIENT-CERT: $CLIENT_PEM" \
	-H "SSL-SERVER-CERT: $SERVER_PEM" \
	--cert client-$NAME.crt \
	http://127.0.0.1:8000/terminal/api/v2/register\?response=$RESPONSE`
RESP_SHA=$1

set `
(
	/bin/echo -n $TAG
	/bin/echo $RESPONSE | xxd -r -p
) | openssl sha256
`
RESP_OK_SHA=$2
if test "x$RESP_OK_SHA" = "x$RESP_SHA"; then
	echo "OK - pairing ok & other side knew tag too"
else
	echo FAIL
	exit 1
fi

exit 0
