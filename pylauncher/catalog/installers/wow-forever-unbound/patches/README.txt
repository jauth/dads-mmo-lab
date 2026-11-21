Patches applied to the unpacked v0.1.36 release source by image/Dockerfile's "source" stage, in name order,
strictly (patch -p1 --forward --batch): a hunk that does not apply stops the build. Each file is pinned by sha256 in
pylauncher/tests/test_forever_unbound_image.py, and each has exactly one reason line below ("<file>: <reason>").

0001-casclib-local-storage-read-only.patch: Lets the map extractor read the player's game folder through a read-only mount, as WoW Forever's image does.
0002-yulon-mentor-script.patch: Adds the Mentor's script, which takes a spell's price before teaching it and never teaches bots.

0001, from forever-bots (byte copy of its /opt/forever/src/build/patches/0001-casclib-local-storage-read-only.patch):
  CascLib opened the client's .build.info and its data files with write access (flags 0 = O_RDWR on Linux) only
  to read them. On a read-only mount of the player's client (Yu'lon mounts it read-only: the folder is theirs)
  the open fails with EROFS, which CascLib reports as FILE_NOT_FOUND, so mapextractor found no storage.
  Four opens now pass STREAM_FLAG_READ_ONLY. Nothing CascLib does on local storage writes those files.

0002, Yu'lon's own:
  A new file, src/server/scripts/Custom/Yulon/yulon_mentor.cpp (npc_yulon_mentor), and one call to it in
  src/server/scripts/Custom/custom_script_loader.cpp. No core file outside scripts/Custom/ changes. The script has
  no data: the gossip option the player picked carries the price (BoxMoney) and the spell (SpellID), from Yu'lon's
  world SQL. The Unbound design is DaddyCool's (Wrath Unbound); no Wrath Unbound code is used.

The patch Yu'lon carried on adde43d (patches-adde43d/0001-playerbot-invite-passing-bots.patch,
Playerbot.Behavior.InvitePassingBots) was adopted upstream in v0.1.36 under the same name (Karrz1/TrinityCore #345).
