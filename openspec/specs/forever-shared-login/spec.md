# forever-shared-login Specification

## Purpose

Defines how several WoW Forever-family servers (entries of the `forevercore` family) share the
client's single login path on one computer: port 1119, the tagged hosts line for
`trinity.actual.battle.net`, and one trusted CA per install.

## Requirements

### Requirement: One Forever-family server runs at a time
Starting a `forevercore` server SHALL be refused while the containers of another `forevercore` install are running. The message SHALL name the running server and say to stop it first. Nothing SHALL be started or changed by the refused start.

#### Scenario: Start Unbound while Forever runs
- **GIVEN** WoW Forever is running
- **WHEN** the player starts WoW Forever Unbound
- **THEN** the start is refused with a message naming WoW Forever, and WoW Forever keeps running

#### Scenario: Switch servers
- **GIVEN** WoW Forever is running
- **WHEN** the player stops WoW Forever and then starts WoW Forever Unbound
- **THEN** WoW Forever Unbound starts and Play logs in to its realm

### Requirement: The hosts line is kept while any Forever-family install remains
Removing a `forevercore` install SHALL remove the tagged `trinity.actual.battle.net` hosts line only when no other `forevercore` install remains, whatever its entry id.

#### Scenario: Remove Unbound, keep Forever
- **GIVEN** WoW Forever and WoW Forever Unbound are both installed
- **WHEN** the player removes WoW Forever Unbound
- **THEN** its own CA is taken out of the trust store, the tagged hosts line stays, and WoW Forever still logs in

#### Scenario: Remove the last one
- **GIVEN** only WoW Forever Unbound is installed
- **WHEN** the player removes it
- **THEN** its CA and the tagged hosts line are both removed

### Requirement: Each install's CA is its own
Each `forevercore` install SHALL trust and remove only the CA thumbprints its own install record holds. Trusting or removing one install's CA SHALL NOT remove another install's CA.

#### Scenario: Play on the second server
- **GIVEN** WoW Forever's CA is trusted
- **WHEN** the player presses Play on WoW Forever Unbound for the first time
- **THEN** WoW Forever Unbound's CA is added and WoW Forever's CA stays trusted

### Requirement: Play targets the running server
Play SHALL set the client's portal, login key and account for the install whose Play was pressed. Play SHALL be refused while a different `forevercore` server is the one running.

#### Scenario: Play the wrong one
- **GIVEN** WoW Forever is running and WoW Forever Unbound is stopped
- **WHEN** the player presses Play on WoW Forever Unbound
- **THEN** Play says WoW Forever is running and must be stopped first, and the game is not started
