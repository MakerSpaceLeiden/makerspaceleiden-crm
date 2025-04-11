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

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" -d amount="1.00" -d hours=20 \
        http://127.0.0.1:8000/pettycredit/api/v1/claim | grep -qp '^[0123456789]'

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" -d amount="zzz" -d hours=20 \
        http://127.0.0.1:8000/pettycredit/api/v1/claim | grep -qi ERROR

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" -d amount="1.23" -d hours=zz \
        http://127.0.0.1:8000/pettycredit/api/v1/claim |grep -qi ERROR

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d uid=4 -d desc="claim test" \
        http://127.0.0.1:8000/pettycredit/api/v1/claim |grep -qi PARAM

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
        -d cid=$CID  -d amount="0" -d desc="false alarm., nothign used"\
        http://127.0.0.1:8000/pettycredit/api/v1/settle | grep -qi OK

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
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi OK

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID -d desc="more time" -d hours=100 \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi OK

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID -d desc="more needed" -d amount="5"\
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi OK

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID -d desc="just txt" \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi OK

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=XX -d desc="just txt" \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi ERROR

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi PARAM

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=XX -d desc="just txt" -d amount=XX \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi ERROR

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=XX -d desc="just txt" -d hours=XX \
        http://127.0.0.1:8000/pettycredit/api/v1/updateclaim | grep -qi ERROR

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        -d cid=$CID  -d amount="3" -d desc="32 minutes of welding gas"\
        http://127.0.0.1:8000/pettycredit/api/v1/settle | grep -qi OK

echo "All OK"
exit 0
