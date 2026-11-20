---
type: Guide
title: "WoW Forever Unbound"
description: "The multi-class WoW Forever realm: its own server beside WoW Forever, the Mentor who teaches other classes' spells, and playing one realm at a time."
tags: [forever, unbound, classic, forevercore, classes, catalog]
resource: pylauncher/yulon/forever_unbound_catalog.py
sources:
  - id: catalog
    resource: pylauncher/yulon/catalog/catalog.json
    title: "The wow-forever-unbound entry"
  - id: spells
    resource: pylauncher/yulon/forever_unbound_catalog.py
    title: "The spells the Mentor teaches"
status: draft
---

# WoW Forever Unbound

WoW Forever (Classic 1.60.1) as a multi-class realm. Your character keeps its own class, and the
Mentor in each capital teaches it spells from other classes. In this first version every spell is
free.[^catalog]

## Its own server, beside WoW Forever

WoW Forever Unbound is a separate server in the Catalog, listed on the WoW card right after WoW
Forever. It has its own folder (`yulon-forever-unbound`), its own containers, its own databases
and its own characters, so installing it never touches your WoW Forever realm.[^catalog]

It uses the same server, the same world and the same bots as WoW Forever. You bring the same
client too: your WoW Forever 1.60.1 game folder (build 70707, or a copy of your Battle.net one at
70888 or 70938). The install makes the maps from that folder, as WoW Forever's does.[^catalog]

## One realm at a time

The game always logs in on the same port, so WoW Forever and WoW Forever Unbound cannot run at
the same time. To switch, press **Stop** on the one that is running, then **Start** (or
**Play**) on the other. If you forget, Yu'lon tells you which server to stop first.[^catalog]

You only say yes to the administrator prompt once: both servers share the login setup that
**Play** adds to your computer.

## The Mentor

The Mentor is a robed figure standing in front of a banker in Stormwind, Ironforge, Darnassus,
Orgrimmar, Undercity and Thunder Bluff. Talk to it and pick a class, then pick a spell. You learn
it on the spot.[^spells]

- **Who can learn:** every class that uses mana: Paladin, Hunter, Priest, Shaman, Mage, Warlock
  and Druid. Your own class is not on the list; you already have a trainer for that.
- **What it teaches:** a few starting spells of each class, such as Frostbolt, Renew, Moonfire,
  Hammer of Justice, Earth Shock, Corruption and Hunter's Mark. Each one appears from the level a
  trainer of that class would teach it.[^spells]
- **Where they go:** the spellbook's **General** tab. Drag them to your action bars like any
  spell. They stay learned when you log out.
- **Warriors and rogues:** these spells cost mana, which warriors and rogues do not have, so the
  Mentor has nothing for them yet. It tells them so.

## Bots

Bots work exactly as on WoW Forever. They never visit the Mentor, so every bot keeps only its own
class's spells. See [Playerbots](/games-and-bots/playerbots-overview.md).

## Limits in this first version

- Only spells, not talents: the talent window still shows your own class.
- No new weapons or armor: what your class can wear is unchanged.
- No spells for warriors and rogues yet.
- No Steam Deck Gaming Mode tiles yet. Play from the app itself.
- The server is a beta in the Catalog.[^catalog]

## If something goes wrong

**"WoW Forever Unbound needs ports …, and WoW Forever is running on one of them."**
Both realms use the same login port. Stop WoW Forever on its tab, then start WoW Forever Unbound
again.

**The Mentor is not there.**
The very first start of the server imports the world, which takes about 15 minutes. The Mentor
appears once that is done. If it is still missing after the server says it is ready, look in the
world server's log for the line that names
`2026_11_20_00_world_yulon_forever_unbound_mentor.sql`. [Logs](/running-a-server/logs.md) shows
where to find it.

**I cannot see a spell in the Mentor's list.**
Three things hide a spell: your character is below the level it needs, you already know it, or it
belongs to your own class. Level up and talk to the Mentor again.

**I learned a spell but cannot cast it.**
Check that it is on an action bar from the spellbook's **General** tab, and that you have the mana
for it.

Other trouble: [Common problems](/getting-started/common-problems.md).

## Credits

The server is ForeverCore, advocaite's Forever core built on TrinityCore, with Karrz's
PlayerbotV2 bots (release 0.1.36). The multi-class idea and the Mentor follow Wrath Unbound by
DaddyCool of Dad's MMO Lab ([WoW Unbound](/games-and-bots/wow-unbound.md)).[^catalog]

[^catalog]: Description, notes, client and platforms from the game catalog.
[^spells]: The Mentor's spell list, levels and classes.
