# Spec Delta

## Purpose

Defines Yu'lon's own WoW Forever Unbound server image: what source it is built from, which core
patches it carries, how it ships its GPL-2 source, and how it is published and pinned.

## ADDED Requirements

### Requirement: Built from WoW Forever's release source
The image SHALL be built from the same ForeverCore release source that WoW Forever's pinned image is built from: the same source archive, by URL and sha256. A ForeverCore release bump for WoW Forever SHALL NOT pass the checks until the Unbound image is rebuilt from the new release.

#### Scenario: Same release
- **WHEN** the catalog and the image recipe are checked
- **THEN** the recipe's source version is the release that WoW Forever's server image is labelled with

#### Scenario: Forever bumped alone
- **GIVEN** WoW Forever's server image moves to a newer release
- **WHEN** the checks run and the Unbound recipe still names the old release
- **THEN** a check fails and names both releases

### Requirement: Core patches are pinned and ordered
The image SHALL apply a fixed, ordered list of patch files to the release source before building. Each patch SHALL be shipped byte for byte as pinned, and each SHALL have a one-sentence reason a player can read. The build SHALL fail if any patch does not apply.

#### Scenario: Patch list
- **WHEN** the patch folder is checked
- **THEN** it holds exactly the listed patches, in order, each matching its pinned sha256

#### Scenario: A patch that no longer applies
- **GIVEN** a release source where one patch's context has changed
- **WHEN** the image is built
- **THEN** the build stops at that patch and no image is produced

### Requirement: The image carries its corresponding source
The image SHALL contain the recipe it was built with and every patch it applied. Its labels SHALL name the release source archive's URL and sha256, the GPL-2.0-only license, and the release version.

#### Scenario: Inspecting the image
- **WHEN** someone inspects the published image
- **THEN** its labels give the source URL, sha256, version and license, and the image holds the Dockerfile and the patch files under its build folder

### Requirement: Published and pinned by digest
The image SHALL be published to `ghcr.io/jauth/forever-unbound` with a tag that names the release and Yu'lon's build number (for example `0.1.36-u1`). The catalog SHALL refer to it only by `@sha256:` digest. The published package SHALL be public, so a player can pull it without signing in.

#### Scenario: Catalog ref
- **WHEN** the catalog is loaded
- **THEN** the `server` image of `wow-forever-unbound` is a `ghcr.io/jauth/forever-unbound@sha256:` reference

#### Scenario: Anonymous pull
- **GIVEN** a computer that has never signed in to GHCR
- **WHEN** WoW Forever Unbound is installed
- **THEN** its server image is pulled at the pinned digest

### Requirement: Bots and the rest of the core are unchanged
Apart from the Mentor's script, the image SHALL behave as WoW Forever's image does: the same bots, the same world database release, the same realm scripts and the same client builds.

#### Scenario: Bots in a group
- **GIVEN** a party of PlayerbotV2 bots on WoW Forever Unbound running Yu'lon's image
- **WHEN** they quest and fight beside the player
- **THEN** they behave as they do on WoW Forever

#### Scenario: Same client builds
- **WHEN** the player's WoW Forever client (build 70707 to 70938) logs in to WoW Forever Unbound
- **THEN** the login succeeds, as it does on WoW Forever
