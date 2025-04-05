# Makerspace Leiden CRM

Welcome to our Makerspace Management System. This software helps our community manage member access, equipment permissions, storage, and more.

## Table of Contents

- [Quick Start Guide](#quick-start-guide)
	- [System Requirements](#system-requirements)
	- [Installation Options](#installation-options)
	- [Accessing the System](#accessing-the-system)
	- [Testing the API](#testing-the-api)
- [For Developers](#for-developers)
- [Functional Requirements](#functional-requirements)
	- [For Trustees (Administrators)](#for-trustees-administrators)
	- [API Features](#api-features)
	- [Self-Service Features](#self-service-features)
	- [Self-Service Bonus](#self-service-bonus)
	- [Email Notifications](#email-notifications)
	- [Operational](#operational)
- [System Design](#system-design)
	- [User Structure](#user-structure)
	- [Key Components](#key-components)

## Quick Start Guide

### System Requirements
- Python (recent version)

### Installation Options

**Option 1: Standard Setup**
1. Make sure you have Python installed on your computer
2. Run the demo script: `sh loaddemo.sh`

**Option 2: Using Poetry**
1. Install [Poetry](https://python-poetry.org/docs/#installation)
2. Create environment file: `cp example.env .env`
3. Run the demo script: `sh loaddemo.sh`

### Accessing the System
After installation, visit:
```
http://localhost:8000/
```

You can log in using the test accounts created during installation. The loaddemo script will output these login details.

### Testing the API
You can test the API with commands like:
```
curl -H "X-Bearer: Foo" -F tag=1-2-4 http://localhost:8000/acl/api/v1/getok4node/foonode
```
(This assumes your local settings contain the "Foo" password - see debug.py)

## For Developers

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information on how to contribute to this project, including code style, pre-commit setup, and submission guidelines.

## Functional Requirements

### For Trustees (Administrators)
- Manage member progression (from new members to full access with 24/7 key)
- Track member status (forms completed, standing in community)
- Manage instruction groups (who can teach others)
- Create and manage equipment/machines
- Manage RFID cards
- Generate reports on storage and permits

### API Features
- Check permissions based on RFID tags
- Verify basic membership
- Verify equipment training status
- Verify specific permits

### Self-Service Features
- New membership requests (no login required)
- Password reset
- Manage RFID cards (activate new cards, deactivate old ones)
- Record when you've given instruction to another member

### Self-Service Bonus
- Report accidents
- Report equipment problems or activate lockouts
- Find member storage bins
- Request storage permits for larger items
- Track spare parts ordering

### Email Notifications
The system automatically sends emails in these situations:

1. **User Detail Changes**
   - When users update their personal information
   - Email sent to: Trustees

2. **Training Records**
   - When someone adds instruction/training records
   - Email sent to: Trustees and possibly members ("deelnemers")

3. **Storage Space Changes**
   - When any changes are made to storage space
   - Email sent to: All members ("deelnemers")
   - Separate email to owner if the change was made by someone else
   - Email to trustees if duration > 30 days or if extending an auto-approved 30-day permit

4. **Storage Box Changes**
   - When any changes are made to storage boxes
   - Email sent to: Trustees
   - Separate email to owner if the change was made by someone else

### Operational
In addition to the above, the system is designed to be easy to maintain and scale.

- Standard Django setup for easy maintenance
- Supports dozens of machines/equipment
- Handles hundreds of users

## System Design

Outline of the current system design.

### User Structure
- Standard Django user system
- Additional member-specific information (forms on file, emergency contacts)
- Possible to add more information

### Key Components
1. **Machines**
   - Equipment and access points (like doors)
   - May require specific training
   - May require signed waivers
   - May require special permits

2. **Permits**
   - Access categories (like door access)
   - May build on other permits

3. **Entitlements**
   - Specific permissions assigned to users
   - Assigned by authorized members
   - Issuers must have the entitlement themselves
   - Instructors need appropriate permits to grant entitlements