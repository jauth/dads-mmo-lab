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

### Requirement: Own server image on WoW Forever's release
WoW Forever Unbound SHALL run Yu'lon's own Forever Unbound server image (see `forever-unbound/server-image`), pinned by `@sha256:`. It SHALL use the same world database release as WoW Forever. Its world content SHALL come from its own SQL files, applied by the server's database updater.

#### Scenario: Image pin
- **WHEN** the catalog is loaded
- **THEN** the `server` image ref of `wow-forever-unbound` is pinned by `@sha256:`, differs from `wow-forever`'s, and both entries name the same world database release

#### Scenario: Content applied at first start
- **WHEN** WoW Forever Unbound's world server starts for the first time
- **THEN** its Unbound world SQL is applied once and the Mentor exists in the world database

### Requirement: An existing install follows the pinned image and files at Start
Starting a stack server SHALL first bring its compose files and Yu'lon's stack files up to the current catalog and templates. When that changes the server's image, Start SHALL pull the pinned image, with its output shown, before starting the containers. Databases, characters, volumes and passwords SHALL be kept. A compose file Yu'lon did not write SHALL be left alone, and Start SHALL be refused with a message saying so.

#### Scenario: Upgrade from the upstream image
- **GIVEN** a WoW Forever Unbound install made with phase 1, running the upstream image, with characters
- **WHEN** the player presses Start after updating Yu'lon
- **THEN** Yu'lon's image is pulled with live output, the server starts on it, the updated Mentor SQL is applied, and every character is still there

#### Scenario: Nothing changed
- **GIVEN** an install whose files already match the catalog
- **WHEN** the player presses Start
- **THEN** no file is rewritten, nothing is pulled, and the server starts as before

#### Scenario: WoW Forever unaffected by Unbound's image
- **WHEN** the player presses Start on WoW Forever
- **THEN** WoW Forever runs its own pinned image, and Yu'lon's Unbound image is neither pulled nor used

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
