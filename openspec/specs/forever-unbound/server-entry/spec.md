# forever-unbound/server-entry Specification

## Purpose

Defines WoW Forever Unbound as its own server option in the launcher: a multi-class WoW Forever
realm that installs, runs and is removed independently of the plain WoW Forever server.

## Requirements

### Requirement: A separate catalog option
The catalog SHALL offer "WoW Forever Unbound" (id `wow-forever-unbound`) as its own single-server entry, separate from "WoW Forever" (`wow-forever`). Both SHALL be installable on the same computer.

#### Scenario: Both options are listed
- **WHEN** the player opens the Catalog
- **THEN** the WoW card lists "WoW Forever" and "WoW Forever Unbound" as two entries after its server cores

#### Scenario: Installing one leaves the other alone
- **GIVEN** WoW Forever is installed
- **WHEN** the player installs WoW Forever Unbound
- **THEN** WoW Forever's folder, containers, volumes, databases, characters and trusted CA are unchanged

### Requirement: Presentation matches the Unbound family
The entry's tile SHALL show the 🌀 glyph, the subtitle "WoW Forever Classic, multi-class" and the server software "ForeverCore with Karrz's PlayerbotV2 bots and Forever Unbound". No player-visible text SHALL use a full trademarked game name.

#### Scenario: Tile text
- **WHEN** the WoW Forever Unbound tile is shown
- **THEN** its glyph, subtitle and software line are the ones above, and its name begins with "WoW"

### Requirement: Own install footprint
WoW Forever Unbound SHALL use its own default folder (`yulon-forever-unbound`), its own container names (`foreverunbound-database`, `-prepare`, `-world`, `-bnet`), its own compose project, volumes and generated passwords, and its own CA.

#### Scenario: No shared names
- **WHEN** both servers are installed
- **THEN** no container, volume, compose project or install folder belongs to both

### Requirement: Same server image as WoW Forever
WoW Forever Unbound SHALL run the same digest-pinned server image and the same world database release as WoW Forever. Its multi-class content SHALL come only from its own SQL files, applied by the server's database updater.

#### Scenario: Image pin
- **WHEN** the catalog is loaded
- **THEN** the `server` image ref of `wow-forever-unbound` equals that of `wow-forever` and is pinned by `@sha256:`

#### Scenario: Content applied at first start
- **WHEN** WoW Forever Unbound's world server starts for the first time
- **THEN** its Unbound world SQL is applied once and the Mentor exists in the world database

### Requirement: Same client and Play as WoW Forever
WoW Forever Unbound SHALL use the player's WoW Forever client and the same Play flow as WoW Forever (login trust, account, key watch). It SHALL NOT write into the client folder anything WoW Forever's Play does not write.

#### Scenario: Play
- **GIVEN** WoW Forever Unbound is installed and running
- **WHEN** the player presses Play
- **THEN** the game starts, logs in to the WoW Forever Unbound realm, and no new file appears in the client folder beyond `_forever_/WTF/ForeverLauncher.wtf`

### Requirement: No Gaming Mode tiles in v1
WoW Forever Unbound SHALL NOT offer "Add to Steam Deck (Gaming Mode)" tiles until the Gaming Mode scripts are made per-entry.

#### Scenario: Gaming Mode offer
- **WHEN** WoW Forever Unbound's server tab is shown on SteamOS
- **THEN** no Gaming Mode tile action is offered for it
