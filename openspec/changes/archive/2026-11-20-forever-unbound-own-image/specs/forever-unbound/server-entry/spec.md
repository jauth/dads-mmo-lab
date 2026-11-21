# Spec Delta

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Same server image as WoW Forever
**Reason**: Mentor prices need C++ in the core, which the upstream `forever-bots` image cannot carry. WoW Forever Unbound now runs Yu'lon's own image, built from the same release source (see "Own server image on WoW Forever's release" and `forever-unbound/server-image`).
**Migration**: Existing installs move to the new image at their next Start ("An existing install follows the pinned image and files at Start"). Characters and databases are kept.
