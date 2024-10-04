Pending payments

1)	Concept of a claim; made by any device that expects the need
	to charge in the future.

	Every claim gets a unique id.

	Eveyr claim has an expiry date in the future.

2)	Device can update the claim with that ID at any time; e.g. to increase
	the amount.

3)	Device can settle the claim with a final amount; which becomes a normal
	transaction.

4)	Any claims that are post their settlement date are auto settled.

5)	A device that tries to settle an already settled claim will generate
	an email to those in a certain CRM group; so that it can be
  	resolved manually. The most likely reason is some node being turned
	off or crashing midway; or some intermittend connectivity issues.

Node behaviour

-	Update your claims when 75% or so has been used.

-	Keep some NVRAM entry to try to settle it after a reboot or
	similar unexpected stuff.

API

[/pettycredit/] api/v1/claim

	Start a claim

	Mandatory
		uid	unqiue user identifier
		amount	amount, in euro's, float
		desc	description, in utf8 or ascii
	Optional
		hours	for how many hours this claim is valid

	Returns a 200 with a claim identifier (opaque ascii string) or an error

[/pettycredit/] api/v1/updateclaim

        Change (e.g. increase) or extend the claim.

	Mandatory
		cid	claim identifier
		amount	(new) amount, in euro's, float
		desc	description, in utf8 or ascii with reason for change
	Optional
		hours	for how many hours this claim is valid

	Returns a 200 or an error

[/pettycredit/] api/v1/settle

	Settle claim.

	Mandatory
		cid	claim identifier
		amount	(new) amount, in euro's, float
		desc	description, in utf8 or ascii

	Returns a 200 or an error
