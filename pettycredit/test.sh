#!/bin/sh
set -e

TMPDIR=${TMPDIR:-/tmp}
cd $TMPDIR

NAME=${NAME:-foo}

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

echo Start a claim
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" -d amount="1.00" -d hours=20 \
        http://127.0.0.1:8000/pettycredit/api/v1/claim

CID=$(curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" -d amount="1.00" \
        http://127.0.0.1:8000/pettycredit/api/v1/claim)

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID -d desc="update claim test" \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID -d desc="more needed" -d amount="5"\
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim


curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID  -d amount="3" -d desc="bit cheaper in the end"\
        http://127.0.0.1:8000/pettycredit/api/v1/settle

exit 0
