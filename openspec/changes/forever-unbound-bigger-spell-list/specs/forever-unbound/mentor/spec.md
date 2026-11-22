# Spec Delta

## MODIFIED Requirements

### Requirement: The Mentor teaches a curated off-class spell list
The Mentor SHALL list spells from a fixed catalog that Yu'lon ships. Each catalog row SHALL name the spell, its rank, the class it comes from, the required character level and the price. The catalog SHALL hold every rank of every curated spell line that the class's trainers teach up to level 60, plus the rank 1 of each class's starting spells.

#### Scenario: Browse by class
- **WHEN** a player talks to the Mentor
- **THEN** the menu offers one submenu per class other than the player's own, and each submenu offers that class's spells in three level bands: spells first learned at levels 1 to 15, from character level 16 at 16 to 30, and from character level 31 at 31 to 60

#### Scenario: A line stays in one band
- **WHEN** a player opens a class's 1 to 15 band at level 60
- **THEN** that band offers the next rank of each line whose rank 1 is learned at level 15 or below, even when that rank is learned above level 15

#### Scenario: Own class not offered
- **WHEN** a mage talks to the Mentor
- **THEN** no mage spells are offered

#### Scenario: Rank shown
- **WHEN** a player opens a band holding a spell with more than one rank
- **THEN** the option names the spell and its rank (for example "Teach me Frostbolt (Rank 3) (35 silver).")

### Requirement: Level and known spells are enforced by the server
The server SHALL NOT show a spell option to a character below the spell's required level, that already knows the spell, or, for a rank above 1, that does not know the rank before it. Such an option cannot be chosen. The server SHALL take money for a Mentor spell only when it teaches that spell.

#### Scenario: Too low
- **WHEN** a level 2 priest opens a list that holds a level 10 spell
- **THEN** that spell is not offered

#### Scenario: Already known
- **GIVEN** a paladin that learned Frostbolt
- **WHEN** the paladin opens the mage list again
- **THEN** Frostbolt is not offered, and the paladin's money is unchanged

#### Scenario: Only the next rank
- **GIVEN** a level 30 paladin who knows Frostbolt ranks 1 and 2
- **WHEN** the paladin opens the mage 1 to 15 band
- **THEN** Frostbolt rank 3 is offered, and no other Frostbolt rank is

#### Scenario: Rank 1 not known
- **GIVEN** a level 30 druid who has never learned Frostbolt
- **WHEN** the druid opens the mage 1 to 15 band
- **THEN** Frostbolt rank 1 is offered, and no higher Frostbolt rank is

### Requirement: Spell prices come from the class's own trainer
Each Mentor spell's price SHALL equal what that spell's own class trainers charge for it on this realm. A starting spell's rank 1, which no trainer teaches, SHALL cost 10 copper. The price SHALL be shown in the Mentor's spell list, beside each spell, before the player picks one, and again in the game's confirm box before the player agrees.

#### Scenario: Price shown in the list
- **WHEN** a player opens a class's spell list at the Mentor
- **THEN** each spell's option shows its price in gold, silver and copper (for example "Teach me Frostbolt (Rank 1) (1 silver).")

#### Scenario: Price shown
- **WHEN** a player picks a Mentor spell
- **THEN** the game shows a confirm box with that spell's price before anything is taken

#### Scenario: Price matches the trainer
- **WHEN** the shipped Mentor data is checked against the world database's trainer data
- **THEN** every Mentor spell that a trainer teaches costs what its class trainer charges for it, and every other Mentor spell is a starting spell's rank 1 costing 10 copper

## ADDED Requirements

### Requirement: Starting spells can be learned
The Mentor SHALL teach rank 1 of each mana class's starting spells that later ranks build on: Fireball, Frost Armor, Smite, Lesser Heal, Holy Light, Seal of Righteousness, Wrath, Healing Touch, Shadow Bolt, Demon Skin, Lightning Bolt, Healing Wave and Raptor Strike. Their later ranks SHALL then be offered like any other rank.

#### Scenario: Fireball for a priest
- **GIVEN** a level 1 priest with at least 10 copper
- **WHEN** the priest picks Fireball at the Mentor
- **THEN** 10 copper is taken, Fireball rank 1 is known, and at level 6 the Mentor offers Fireball rank 2

### Requirement: No Mentor menu exceeds the gossip limit
No Mentor menu SHALL show a character more than 32 options at once, whatever the character's level and class, for any character whose off-class ranks were learned in order, as the Mentor teaches them. The shipped catalog SHALL guarantee this by counting, in each band, every line and every branch that can show a rank at the same time.

#### Scenario: Level 60 with nothing learned
- **GIVEN** a level 60 character of any mana class who has learned nothing from the Mentor
- **WHEN** the character opens every class band
- **THEN** every band opens, none shows more than 32 options, and the world server keeps running

#### Scenario: Checked on the shipped data
- **WHEN** the shipped catalog is checked
- **THEN** no band holds more than 32 lines and branches (a branch is a spell that follows a rank another spell also follows, such as Create Soulstone after Drain Soul)

### Requirement: Excluded spell lines are recorded
A spell line that its class's trainers teach but the catalog leaves out SHALL be recorded with its reason: power cost, stance, form, pet, totem, ranged weapon, armor or weapon skill, or a first rank no trainer teaches (talent or quest).

#### Scenario: Talent line
- **WHEN** the curation record is read
- **THEN** a talent line such as Pyroblast is listed as left out because its first rank is a talent
