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
FQDN=${IP:-127.0.0.1}

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
	http://$FQDN:8000/pettycash/api/v1/pay | jq

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d src=${TAG} \
        -d amount=1.00 \
        -d description="25 grammes of red PLA (new API, node ${NAME})" \
	http://$FQDN:8000/pettycash/api/v2/pay | jq

NONCE=$(curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d uid=6 \
        -d amount=2.00 \
        -d description="TIG Welder, Argon gas" \
	http://$FQDN:8000/pettycash/api/v2/claim_create)

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=4.00 \
        -d comment="Used 2.00 euro, updating claim" \
	http://$FQDN:8000/pettycash/api/v2/claim_update | grep -q $NONCE

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=3.10 \
        -d description="Welding gas; 72 minutes; 210 Liters" \
        -d comment="Welder powered own" \
	http://$FQDN:8000/pettycash/api/v2/claim_settle  | grep -q Settled

# Try to update an already closed claim - and check it errors
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=4.00 \
        -d comment="Should fail - updating closed claim" \
	http://$FQDN:8000/pettycash/api/v2/claim_update | grep -q 'Claim already settled'

# Try to settle a closed claim twice - and check that it errors
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=3.10 \
        -d description="Welding gas; 72 minutes; 210 Liters" \
        -d comment="Try to settle a settled claim" \
	http://$FQDN:8000/pettycash/api/v2/claim_settle  | grep -q "Claim already settled"

# try to update a nonexistent claim
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=XX$NONCE \
        -d comment="Should fail - does not exist" \
	http://$FQDN:8000/pettycash/api/v2/claim_update | grep -q 'Claim problem'

# try to settle a nonexistent claim
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=XX$NONCE \
        -d comment="Should fail - does not exist" \
	http://$FQDN:8000/pettycash/api/v2/claim_settle| grep -q 'Claim problem'

# Create a non auto setttling claim
NONCE=$(curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d uid=6 \
        -d amount=2.00 \
        -d settleInSeconds=0 \
        -d description="Pottery, non settling" \
	http://$FQDN:8000/pettycash/api/v2/claim_create)

curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=3.10 \
        -d description="Pottery, settle" \
        -d comment="done" \
	http://$FQDN:8000/pettycash/api/v2/claim_settle  | grep -q Settled

# Create a non auto setttling claim - and leave it dangling
NONCE=$(curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d uid=6 \
        -d amount=2.00 \
        -d settleInSeconds=0 \
        -d description="Pottery, non settling" \
	http://$FQDN:8000/pettycash/api/v2/claim_create)
# Update the non-settler; and that is it.
curl --silent \
        -H "X-FORWARDED-FOR: ${IP}"  \
        -H "SSL-CLIENT-CERT: $CLIENT_PEM" \
        -H "SSL-SERVER-CERT: $SERVER_PEM" \
        --cert client-$NAME.crt \
        -d claim=$NONCE \
        -d amount=4.00 \
        -d comment="I think we are done - but not clsing yet" \
        http://$FQDN:8000/pettycash/api/v2/claim_update | grep -q $NONCE

echo OK
