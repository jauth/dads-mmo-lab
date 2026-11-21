#!/usr/bin/env bash
# Unpacks the world and hotfixes database release into /srv/tdb, where worldserver (working directory /srv/tdb)
# finds it and imports it on its first start. Runs at every start; does nothing once the .sql files are there.
source /opt/forever/yulon/common.sh
T=/srv/tdb
mkdir -p "$T"
if ls "$T"/TDB_full_world_*.sql >/dev/null 2>&1 && ls "$T"/TDB_full_hotfixes_*.sql >/dev/null 2>&1; then
  say "world database release ready"; exit 0
fi
archive=$(ls /srv/downloads/TDB_full_*.7z 2>/dev/null | head -1 || true)
[ -n "$archive" ] || { say "no TDB_full_*.7z in the install's downloads folder: run Install again"; exit 3; }
say "unpacking $(basename "$archive")"
7z x -y -o"$T" "$archive" >/dev/null
ls "$T"/TDB_full_world_*.sql >/dev/null && ls "$T"/TDB_full_hotfixes_*.sql >/dev/null
say "world database release ready"
