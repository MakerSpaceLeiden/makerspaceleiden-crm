# Quick test/install

-	Make sure you have a somewhat recent python version

-   [OPTIONAL] If you want to use `poetry` instead, install [poetry](https://python-poetry.org/docs/#installation)
    - Add environment variable `POETRY` with the value true. Can be done by running: `cp example.env .env`

-	sh loaddemo.sh

Then go to

	http://localhost:8000/

and login using the accounts created & shown to you during the loaddemo.sh script.

# Requirements

## Trustees
-	Create member, progress status from initial to full (i.e. with 24x7 key)

-	Checkboxes for things such as 'form on file', member-in-good-standing

-	Management of groups (e.g. people that can give instruction)

-	Creation of new machines and groups

-	Overview rfid cards

-	Reports on bins & (big/overdue) storage permits.

## API

-	lists or OK/deny on tag's.
		based on just being a member
		based on having had instructions
		based on an actual permit

## Self service

-	Initial contact / request membership (no auth)

-	password reset.

-	activate (new) card, retire old.

-	record whom you have given instruction to.


## Self service (bonus)

-	report accident

- 	report outages
	activate lockout

-	location members bin
		visible to all

-	storage permits & durations for things that do not fit in the members bin.
		request
		visible to all

-	track ordering of spares.

## Non functional requirements

- Very 'standard' approach - so ops and code evolving does not rely on a few skilled people.
- Some 10's of machines
- Low 100's of users

## Email 'rules'

- User changes his/her details -> email trustees
- Someone adds instructions -> email trustees ? deelnemers ?
- Any mutations on storage space - email deelnemers
  Email owner separare if the change is made by someone else but the owner.
  Email trusteeds if > 30 days or extension on a auto-approve 30 days.
- Box changes - email trusteeds
  Email owner separare if the change is made by someone else but the owner.

# Current design

- Normal Django users; Members adds a field to that (form on file). May
	add more in the future (e.g. emergency contact).

- Machines
	Machines or things that you can interact with (like doors).
	May require instructions
	May require the waiver to be on file.
	May require a 'permit' of a specific type.

- Permits
	E.g. allowed to open doors.
	May require a permit to be issued (one deep)

- Entitlements
	of a specific permi
	Assigned to a user (owner) by an issuer.
	issuer must have the entitlement himself.
	issuer must ALSO have the permit specified in the permit,
	i.e. the instruction permit, if so specified (one deep)

## issues with the current design
