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

	-	callback with a NONCE (there is no opaque reference/transaction field)

	-	own transaction reference in the human readable description

		investiage checkout_reference in checkout (not card type)

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



