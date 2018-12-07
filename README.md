
Requirements

Trustees
-	Create member, progress status from initial to full (i.e. with 24x7 key)

-	Checkboxes for things such as 'form on file', member-in-good-standing

-	Management of groups (e.g. people that can give instruction)

-	Creation of new machines and groups

-	Overview rfid cards

-	Reports on bins & (big/overdue) storage permits.

API

-	lists or OK/deny on tag's.
		based on just being a member
		based on having had instructions
		based on an actual permit

Self service

-	Initial contact / request membership (no auth)

-	password reset.

-	activate (new) card, retire old.

-	record whom you have given instruction to.


Self service (bonus)

-	report accident 

- 	report outages
	activate lockout

-	location members bin
		visible to all

-	storage permits & durations for things that do not fit in the members bin.
		request
		visible to all

-	track ordering of spares.

= Current design

Normal Django users; Members adds a field to that (form on file). May
	add more in the future (e.g. emergency contact). Another
	option would be to use the more modern AbstractBaseUser.

Machines
	Machines or things that you can interact with (like doors).
	May require instructions
	May require the waiver to be on file.
	May require a 'permit' of a specific type.

Permits
	E.g. allowed to open doors.

Instructions
	member can give & record instructions
	but only on the things they have received instruction on.

Entitlements
	heavier version of an instruction - connects a member to
	an permit. Permits can span multiple devices (unlike
	instructions). 

	Assumption is that only a few peple add these.

Issues
	Members extenion of Users is messy.
	
	Instructions and permits too similar.

	Unclear approval workflow for Entitlements; e.g. explicit
	ok from both instructor and trustee ? Or do we use
	the second layer instructions for this ?
