# forever-unbound/mentor Specification

## Purpose

Defines the Mentor, the NPC through which a WoW Forever Unbound character learns spells from
classes other than its own, and the rules that decide what it may learn.

## Requirements

### Requirement: The Mentor is in every capital
The world SHALL hold one Mentor in each of the six Classic capitals: Stormwind, Ironforge, Darnassus, Orgrimmar, Undercity and Thunder Bluff. Each SHALL be reachable by either faction's players in its own city.

#### Scenario: Find the Mentor
- **WHEN** a player enters any of the six capitals on WoW Forever Unbound
- **THEN** a creature named "The Mentor" stands there and offers a gossip menu

### Requirement: The Mentor teaches a curated off-class spell list
The Mentor SHALL list spells from a fixed catalog that Yu'lon ships. Each catalog row SHALL name the spell, the class it comes from and the required character level. In v1 every spell is taught free of charge.

#### Scenario: Browse by class
- **WHEN** a player talks to the Mentor
- **THEN** the menu offers one submenu per class other than the player's own, and each submenu lists that class's catalog spells

#### Scenario: Own class not offered
- **WHEN** a mage talks to the Mentor
- **THEN** no mage spells are offered

### Requirement: Only spells the character can power
In v1, the catalog SHALL hold only spells that cost mana or no power. The Mentor SHALL offer them only to characters whose class has mana (Paladin, Hunter, Priest, Shaman, Mage, Warlock, Druid). Warriors and Rogues SHALL be told the Mentor has nothing for them yet.

#### Scenario: Warrior
- **WHEN** a warrior talks to the Mentor
- **THEN** the Mentor says it has nothing to teach a warrior yet, and offers no spells

#### Scenario: Paladin learns Frostbolt
- **GIVEN** a level 4 or higher paladin
- **WHEN** the paladin chooses Frostbolt at the Mentor
- **THEN** no money is taken, Frostbolt is known, and casting it on a target deals damage and costs the paladin's mana

### Requirement: Level and known spells are enforced by the server
The server SHALL NOT show a spell option to a character below the spell's required level or that already knows the spell, so it cannot be chosen. The server SHALL NOT take money for any Mentor spell.

#### Scenario: Too low
- **WHEN** a level 2 priest opens a list that holds a level 10 spell
- **THEN** that spell is not offered

#### Scenario: Already known
- **GIVEN** a paladin that learned Frostbolt
- **WHEN** the paladin opens the mage list again
- **THEN** Frostbolt is not offered, and the paladin's money is unchanged

### Requirement: Learned spells persist
A spell bought from the Mentor SHALL stay known across logout, login and server restarts.

#### Scenario: Relog
- **GIVEN** a druid that learned Frostbolt from the Mentor
- **WHEN** the player logs out, restarts the server and logs back in
- **THEN** the druid still knows Frostbolt and can cast it

### Requirement: Bots are not multi-class
PlayerbotV2 bots SHALL NOT learn spells from the Mentor, and their class behavior SHALL match WoW Forever's.

#### Scenario: Party bot beside a multi-class player
- **GIVEN** a priest who learned Frostbolt from the Mentor and has a party of bots
- **WHEN** the party fights
- **THEN** every bot knows only its own class's spells, as on WoW Forever

### Requirement: Mentor content is self-contained
The Mentor's world rows SHALL use only ID ranges Yu'lon reserves for Forever Unbound: creature template, spawn GUIDs, gossip menus and text, server-side spells and SmartAI rows. Applying them SHALL NOT change any row the world database release or ForeverCore's own updates own.

#### Scenario: Reserved ranges
- **WHEN** the Unbound world SQL is applied to a fresh world database
- **THEN** every row it inserts or deletes has an ID inside Yu'lon's reserved ranges, and none of those IDs existed before
