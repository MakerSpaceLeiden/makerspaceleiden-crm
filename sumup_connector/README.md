Workflow /idea 1	 - Deposit only

	First
		Set/press rotary knob or a set of 5 buttons with the amounts 5, 10, 25 and 50 euro

	Second
		Swipe your personal tag on a the reader

	Third
		The Sumup terminal wakes up; and you have 60 seconds to tap/insert a debit card, creditcard, apple-pay, whatever.

	Fourth
		The Sumup terminal says Ok/fail

	Fifth
		You get an email with a confirmation; money is visible in the CRM

Extra feature
	Unit makes a bit of noise if someone enters whose account is < 5 euro and a lot of noise if you are well below 0.

Design

-	Node at space calls API on CRM

-	CRM pushes to sumup API with

	-	callback with an my transaction id  (there is no opaque reference/transaction field)

	-	protect this with a timestamp and a hash of timestamp/id - as to be able to block fake submissions cheap

	-	own transaction reference in the human readable description - so they ae visible in the interface of sumup

-	On callback - processes it against the petty cash

-	Every day - runs a transaction check on the sumup API
		: SUCCESSFUL CANCELLED FAILED PENDING

	-	email treasurer if there is a discrepancy

	-	email on any FAILED or PENDING

	-	email on any REFUND or CHARGE_BACK
			assume manual fix by treasuer for now

-	Every week (later month) - runs a transaction check on the sumup API

	-	list REFUND
			assume manual fix by treasuer for now

	-	list CHARGE_BACK
			assume manual fix by treasuer for now

	-	delete dangling/incompleted transactions

		add to report for treasuer as a simple FYI

	-	count  on the 4 possibilities

Also available per transaction

	CANCELLED 	- reporting
	SUCCESSFUL 	- can be added to petty cash
	PAID_OUT 	- ok to delete the record; we're fully done ?
	CANCEL_FAILED 	??
	FAILED
	REFUND_FAILED
	recall ?
		CHARGEBACK
		REFUNDED
		NON_COLLECTION


Know responses

*) Reader waiting for input/paument

	{'data': {'client_transaction_id': '6ed7cebb-a1b5-4168-bd9a-a82bc8c4f329'}}

*) Reader offline or switched off

	client.readers.create_checkout
	1)	Unprocessable Entity 
		422
		{"errors":{"detail":"The device is offline.","type":"READER_OFFLINE"}}

        no callback
 
*) Timeout on reader
	callback with

	{
	  "id": "e7676090-69e9-42d7-a4bc-7d48d58aad01",
	  "event_type": "solo.transaction.updated",
	  "payload": {
	    "client_transaction_id": "6ed7cebb-a1b5-4168-bd9a-a82bc8c4f329",
	    "merchant_code": "XXXX",
	    "status": "failed",
	    "transaction_id": null
	  },
	  "timestamp": "2025-09-30T10:45:18.479781Z"
	}

*) User cancled on reader

	callback with
	{
		  "id": "4fde97be-1ec5-4a8d-8a86-b30814c9b18c",
		  "event_type": "solo.transaction.updated",
		  "payload": {
		    "client_transaction_id": "a95e1d75-156b-4e18-a5d9-68005b4c0677",
		    "merchant_code": "XXXXXXX",
		    "status": "failed",
		    "transaction_id": null
		  },
		  "timestamp": "2025-09-30T10:46:35.231141Z"
	}

c) Request while reader is already waiting for a payment:

	client.readers.create_checkout
	1) Unprocessable Entity 
	   422 
           {"errors":{"detail":"Unprocessable Entity"}}

d) Successful payment

	        {'data': {'client_transaction_id': '6ed7cebb-a1b5-4168-bd9a-a82bc8c4f329'}}

	on submission; and callback of below

        {
          "id": "97306a5f-4d99-4ffc-9737-d0c50c8c8a0b",
          "event_type": "solo.transaction.updated",
          "payload": {
            "client_transaction_id": "6ed7cebb-a1b5-4168-bd9a-a82bc8c4f329",
            "merchant_code": "XXXXXXX",
            "status": "successful",
            "transaction_id": null
          },
          "timestamp": "2025-09-25T18:07:36.545397Z"

*) It is possible (e.g during startup or when the connectvity is flaky) to get a 

	   {'data': {'client_transaction_id': '6ed7cebb-a1b5-4168-bd9a-a82bc8c4f329'}}

	back as if the reader is asking for payment (but it is not) and no callback
	after 60 seconds/timeout.

Know issues

-	if you do not reply to the callback with a 200 -- e.g. a 5xx or 4xx - it seems
	that it keeps retrying for at least 8 hours;first every few minutes and dropping
        to every 4 hours. We may need to respond to wrong hashes with a OK

-	the callbacks can come minutes later if ??they are busy???

-	Sometimes a transaction clears - but the transaction_id is Null.
	A few seconds later - a list transdaction call will show it.
	Know issue: https://github.com/sumup/sumup-android-sdk/issues/195 
	from 2024
 
py-SumIP - https://github.com/sumup/sumup-py

-      based on pydantic - with strict schema's. Violates the internet/
       architecture maxim of be strict of what you sent, leisure on what
       you expect. Important as the SumUP API is relatively bloated and
       context/culture sensitive & exposes such with little abstraction.
       Already broke on one (https://github.com/sumup/sumup-py/issues/76)
       ease/fundamental case.

      In the critical path in 3 places

       1) pass through on initial submit; situation not too bad
          as the data is fairly trivial/simple; but risk when
	  they start to enrich user information feedback

       2) callback - not an issue - parsing that ourselves

       3) trnsaction crossref - main risk - any improvement
          in the api will break the pydantic checks

      other places are under interactive human control. 

      API is fairly trivial (bearer token, URL with merchant code 
      and json bodies). So perhaps, once it works, replace just
      those 2 (1&3) by our own; but levave the code in the
      management utils for pairing/etc as thare not ran
      unsupervised / not in a time critical workflow and/or
      can be ran repeatedly.

