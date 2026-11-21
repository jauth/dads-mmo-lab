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
The Mentor SHALL list spells from a fixed catalog that Yu'lon ships. Each catalog row SHALL name the spell, the class it comes from, the required character level and the price.

#### Scenario: Browse by class
- **WHEN** a player talks to the Mentor
- **THEN** the menu offers one submenu per class other than the player's own, and each submenu lists that class's catalog spells

#### Scenario: Own class not offered
- **WHEN** a mage talks to the Mentor
- **THEN** no mage spells are offered

### Requirement: Only spells the character can power
The catalog SHALL hold only spells that cost mana or no power. The Mentor SHALL offer them only to characters whose class has mana (Paladin, Hunter, Priest, Shaman, Mage, Warlock, Druid). Warriors and Rogues SHALL be told the Mentor has nothing for them yet.

#### Scenario: Warrior
- **WHEN** a warrior talks to the Mentor
- **THEN** the Mentor says it has nothing to teach a warrior yet, and offers no spells

#### Scenario: Paladin learns Frostbolt
- **GIVEN** a level 4 or higher paladin with enough money
- **WHEN** the paladin chooses Frostbolt at the Mentor
- **THEN** Frostbolt's price is taken, Frostbolt is known, and casting it on a target deals damage and costs the paladin's mana

### Requirement: Level and known spells are enforced by the server
The server SHALL NOT show a spell option to a character below the spell's required level or that already knows the spell, so it cannot be chosen. The server SHALL take money for a Mentor spell only when it teaches that spell.

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
PlayerbotV2 bots SHALL NOT learn spells from the Mentor, and their class behavior SHALL match WoW Forever's. The server SHALL refuse a Mentor spell to a bot's session, even if one picks it, and take nothing.

#### Scenario: Party bot beside a multi-class player
- **GIVEN** a priest who learned Frostbolt from the Mentor and has a party of bots
- **WHEN** the party fights
- **THEN** every bot knows only its own class's spells, as on WoW Forever

#### Scenario: A bot picks a Mentor spell
- **WHEN** a bot's session selects a Mentor spell option
- **THEN** nothing is learned and no money is taken

### Requirement: Mentor content is self-contained
The Mentor's world rows SHALL use only ID ranges Yu'lon reserves for Forever Unbound: creature template, spawn GUIDs, and gossip menus and text. Applying them SHALL NOT change any row the world database release or ForeverCore's own updates own. Rows the Mentor no longer uses SHALL be removed from its reserved ranges when its SQL is applied.

#### Scenario: Reserved ranges
- **WHEN** the Unbound world SQL is applied to a fresh world database
- **THEN** every row it inserts or deletes has an ID inside Yu'lon's reserved ranges, and none of those IDs existed before

#### Scenario: Upgrade from phase 1's rows
- **GIVEN** a world database holding phase 1's Mentor rows, including its server-side teach spells and SmartAI rows
- **WHEN** the new Unbound world SQL is applied
- **THEN** no server-side teach spell or SmartAI row remains in the Mentor's reserved ranges, and the Mentor teaches through its script

### Requirement: The price is paid before the spell is taught
When a character picks a spell at the Mentor, the server SHALL check that the character can afford the spell's price, take exactly that much money, and then teach the spell. If the character cannot afford it, the server SHALL take nothing and teach nothing. A spell the character already knows SHALL NOT be charged for again.

#### Scenario: Enough money
- **GIVEN** a level 4 paladin with more money than Frostbolt's price
- **WHEN** the paladin picks Frostbolt at the Mentor and confirms the price
- **THEN** the price is taken from the paladin's money, and Frostbolt is known

#### Scenario: Not enough money
- **GIVEN** a level 4 paladin with less money than Frostbolt's price
- **WHEN** the paladin picks Frostbolt and confirms
- **THEN** the game says there is not enough money, the paladin's money is unchanged, and Frostbolt is not known

#### Scenario: Learned elsewhere while the menu was open
- **GIVEN** a druid with the mage list open who learns Frostbolt by other means before choosing it
- **WHEN** the druid picks Frostbolt in the open list
- **THEN** no money is taken

### Requirement: Spell prices come from the class's own trainer
Each Mentor spell's price SHALL equal what that spell's own class trainers charge for it on this realm. The price SHALL be shown in the Mentor's spell list, beside each spell, before the player picks one, and again in the game's confirm box before the player agrees.

#### Scenario: Price shown in the list
- **WHEN** a player opens a class's spell list at the Mentor
- **THEN** each spell's option shows its price in gold, silver and copper (for example "Teach me Frostbolt (1 silver).")

#### Scenario: Price shown
- **WHEN** a player picks a Mentor spell
- **THEN** the game shows a confirm box with that spell's price before anything is taken

#### Scenario: Price matches the trainer
- **WHEN** the shipped Mentor data is checked against the world database's trainer data
- **THEN** every Mentor spell's price equals its class trainer's cost for that spell
