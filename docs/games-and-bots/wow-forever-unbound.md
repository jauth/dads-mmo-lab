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
  - id: image
    resource: pylauncher/catalog/installers/wow-forever-unbound/image/README.md
    title: "WoW Forever Unbound's server image"
status: draft
---

# WoW Forever Unbound

WoW Forever (Classic 1.60.1) as a multi-class realm. Your character keeps its own class, and the
Mentor in each capital teaches it spells from other classes, for the same price that class's own
trainer charges.[^catalog]

## Its own server, beside WoW Forever

WoW Forever Unbound is a separate server in the Catalog, listed on the WoW card right after WoW
Forever. It has its own folder (`yulon-forever-unbound`), its own containers, its own databases
and its own characters, so installing it never touches your WoW Forever realm.[^catalog]

It runs the same world and the same bots as WoW Forever, on its own copy of the server: WoW
Forever's server built from the same source, plus the Mentor's own code. That server is a separate
download of about 4 GB, so having both realms takes about 4 GB more disk space than WoW Forever
alone.[^image]

You bring the same client too: your WoW Forever 1.60.1 game folder (build 70707, or a copy of your
Battle.net one at 70888 or 70938). The install makes the maps from that folder, as WoW Forever's
does.[^catalog]

## Updating

When a new Yu'lon brings a new version of the server, the next **Start** downloads it before the
server starts, and the console shows the download. Your characters, their spells and their gold
are kept. Only that first Start takes longer.

## One realm at a time

The game always logs in on the same port, so WoW Forever and WoW Forever Unbound cannot run at
the same time. To switch, press **Stop** on the one that is running, then **Start** (or
**Play**) on the other. If you forget, Yu'lon tells you which server to stop first.[^catalog]

You only say yes to the administrator prompt once: both servers share the login setup that
**Play** adds to your computer.

## The Mentor

The Mentor is a robed figure standing in front of a banker in Stormwind, Ironforge, Darnassus,
Orgrimmar, Undercity and Thunder Bluff. Talk to it and pick a class, then pick a spell. Each spell
in the list shows its price, for example "Teach me Frostbolt (1 silver)." The game asks you to
confirm and shows the price again. Say yes, and the money is taken and you learn the spell on
the spot.[^spells]

- **Who can learn:** every class that uses mana: Paladin, Hunter, Priest, Shaman, Mage, Warlock
  and Druid. Your own class is not on the list; you already have a trainer for that.
- **What it teaches:** a few starting spells of each class, such as Frostbolt, Renew, Moonfire,
  Hammer of Justice, Earth Shock, Corruption and Hunter's Mark. Each one appears from the level a
  trainer of that class would teach it.[^spells]
- **What it costs:** the same as at that class's trainer, from 10 copper for a level 1 spell to a
  few silver. If you cannot pay, the game says so, and nothing is taken.[^spells]
- **Where they go:** the spellbook's **General** tab. Drag them to your action bars like any
  spell. They stay learned when you log out.
- **Warriors and rogues:** these spells cost mana, which warriors and rogues do not have, so the
  Mentor has nothing for them yet. It tells them so.

## Bots

Bots work exactly as on WoW Forever. They never visit the Mentor, so every bot keeps only its own
class's spells. See [Playerbots](/games-and-bots/playerbots-overview.md).

## Limits for now

- A short list of starting spells. A bigger list, with more spells and higher levels, is planned.
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

**"Not enough money" when I pick a spell.**
Each spell costs what its class's trainer charges. Earn a little more and come back; nothing was
taken.

**The first Start after updating Yu'lon takes a long time.**
It is downloading the new server, about 4 GB; the console shows the progress. Later Starts are
quick again.

**Start says it "could not download its server".**
Check your internet connection and press **Start** again. The download picks up where it stopped,
and your realm is unchanged until it finishes.

**I cannot see a spell in the Mentor's list.**
Three things hide a spell: your character is below the level it needs, you already know it, or it
belongs to your own class. Level up and talk to the Mentor again.

**I learned a spell but cannot cast it.**
Check that it is on an action bar from the spellbook's **General** tab, and that you have the mana
for it.

Other trouble: [Common problems](/getting-started/common-problems.md).

## Credits

The server is ForeverCore, advocaite's Forever core built on TrinityCore, with Karrz's
PlayerbotV2 bots (release 0.1.36). Yu'lon builds it with one small addition, the Mentor's code; its
source and that change come with the server (GPL-2).[^image] The multi-class idea and the Mentor
follow Wrath Unbound by DaddyCool of Dad's MMO Lab
([WoW Unbound](/games-and-bots/wow-unbound.md)).[^catalog]

[^catalog]: Description, notes, client and platforms from the game catalog.
[^spells]: The Mentor's spell list, levels, classes and prices.
[^image]: How WoW Forever Unbound's server is built, what it adds and where its source is.
