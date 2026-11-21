#!/usr/bin/env bash
# Extracts the server's game data from the player's own WoW Forever client (mounted read-only at /client) into
# /srv/data: mapextractor (dbc, gt, Cameras, maps), vmap4extractor + vmap4assembler (vmaps), mmaps_generator (mmaps).
# Karrz's repack does the same with its Windows tools (extract_client_data.ps1). Each finished step leaves a marker,
# so a second run (Install pressed again, or "Re-extract") picks up where the last one stopped.
# Map data is never downloaded: it comes from each player's own client.
source /opt/forever/yulon/common.sh
IN=/client
OUT=/srv/data
BIN=/opt/forever/bin
THREADS=${THREADS:-$(nproc)}
LOCALE=${LOCALE:-enUS}
[ -f "$IN/_forever_/Wow.exe" ] || { say "no _forever_/Wow.exe in the client folder"; exit 4; }
mkdir -p "$OUT"
cd "$OUT"
done_() { [ -f "$OUT/.yulon-$1.done" ]; }
mark() { date -u +%FT%TZ > "$OUT/.yulon-$1.done"; }
clock=$SECONDS

# map_gx_gy tiles of the start zones worldserver checks before it starts (World.cpp ExistMapAndVMap)
START_TILES="0000_43_31 0000_48_32 0001_33_39 0000_28_28 0001_12_30 0001_37_32"

if done_ maps; then say "step 1/4 maps: already done"; else
  say "step 1/4: mapextractor (maps, dbc, Cameras, gt)"
  "$BIN/mapextractor" -i "$IN" -o "$OUT" -e 15 -f 1 -l "$LOCALE" -p wowf
  for t in $START_TILES; do [ -f "maps/$t.map" ] || { say "mapextractor wrote no maps/$t.map"; exit 5; }; done
  mark maps
fi
if done_ vmaps; then say "step 2-3/4 vmaps: already done"; else
  rm -rf Buildings dir_bin
  say "step 2/4: vmap4extractor (Buildings)"
  "$BIN/vmap4extractor" -d "$IN" -p wowf --threads "$THREADS" || "$BIN/vmap4extractor" -d "$IN" -p wowf --threads 1
  say "step 3/4: vmap4assembler (vmaps)"
  mkdir -p vmaps
  "$BIN/vmap4assembler" Buildings vmaps --threads "$THREADS"
  [ -f vmaps/0000/0000.vmtree ] || ls vmaps/0000/*.vmtree >/dev/null 2>&1 || { say "vmap4assembler wrote no vmaps/0000"; exit 6; }
  mark vmaps
fi
if done_ mmaps; then say "step 4/4 mmaps: already done"; else
  say "step 4/4: mmaps_generator (pathfinding for the bots; the longest step)"
  mkdir -p mmaps
  "$BIN/mmaps_generator" --input "$OUT" --output "$OUT" --silent --threads "$THREADS"
  ls mmaps/*.mmap >/dev/null 2>&1 || { say "mmaps_generator wrote no mmaps"; exit 7; }
  mark mmaps
fi
rm -rf Buildings dir_bin
say "map data ready: $(du -sh "$OUT" | cut -f1) in $(( (SECONDS - clock) / 60 )) minutes"
