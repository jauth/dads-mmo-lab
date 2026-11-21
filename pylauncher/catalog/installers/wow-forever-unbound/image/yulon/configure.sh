#!/usr/bin/env bash
# Writes /srv/etc from the .dist files in this image, changing only what a local realm in Docker needs.
# Runs at every start (compose service "configure", before the servers): the first time it copies the .dist files;
# after that it keeps the player's own edits and re-sets only the keys Yu'lon owns (database login, paths, ports),
# so a new password or port reaches the servers. zz-zz-yulon.conf is Yu'lon's and is rewritten each time:
# worldserver reads worldserver.conf.d in sorted name order and the last value wins, so it sorts after
# every zz-forever-*.conf; a player's own overrides go in a file that sorts after it (zz-zz-zz-mine.conf).
source /opt/forever/yulon/common.sh
need DB_PASSWORD
DB_HOST=${DB_HOST:-database}
DB_USER=${DB_USER:-trinity}
REST_PORT=${REST_PORT:-8081}
DIST=/opt/forever/etc
ETC=/srv/etc
mkdir -p "$ETC/worldserver.conf.d"

BNET=$ETC/bnetserver.conf
WORLD=$ETC/worldserver.conf
[ -f "$BNET" ] || { cp "$DIST/bnetserver.conf.dist" "$BNET"; say "wrote bnetserver.conf from the image"; }
[ -f "$WORLD" ] || { cp "$DIST/worldserver.conf.dist" "$WORLD"; say "wrote worldserver.conf from the image"; }

db() { printf '"%s;3306;%s;%s;%s"' "$DB_HOST" "$DB_USER" "$DB_PASSWORD" "$1"; }

setkey "$BNET" LoginDatabaseInfo "$(db auth)"
setkey "$BNET" BindIP '"0.0.0.0"'
setkey "$BNET" LoginREST.Port "$REST_PORT"
setkey "$BNET" LoginREST.ExternalAddress trinity.actual.battle.net
setkey "$BNET" LoginREST.LocalAddress trinity.actual.battle.net
setkey "$BNET" CertificatesFile '"/srv/certs/chain.pem"'
setkey "$BNET" PrivateKeyFile '"/srv/certs/server.key"'
setkey "$BNET" LogsDir '"/srv/logs"'
setkey "$BNET" Realm.CfgContentSetID 137
setkey "$BNET" Realm.SuperDistrictID 2
# The realm runs build 70707; Karrz's release lets these later builds of the same game data in (each has its
# auth.build_info row in sql/custom/auth), so a copy of a Battle.net client at one of them plays too.
ALSO_ACCEPT_BUILDS=${ALSO_ACCEPT_BUILDS-70755,70790,70840,70862,70888,70938}
setkey "$BNET" Realm.AlsoAcceptBuilds "\"$ALSO_ACCEPT_BUILDS\""

setkey "$WORLD" LoginDatabaseInfo "$(db auth)"
setkey "$WORLD" WorldDatabaseInfo "$(db world)"
setkey "$WORLD" CharacterDatabaseInfo "$(db characters)"
setkey "$WORLD" HotfixDatabaseInfo "$(db hotfixes)"
setkey "$WORLD" RealmID 70
setkey "$WORLD" BindIP '"0.0.0.0"'
setkey "$WORLD" DataDir '"/srv/data"'
setkey "$WORLD" LogsDir '"/srv/logs"'
setkey "$WORLD" SourceDirectory '"/opt/forever/src"'
setkey "$WORLD" Network.SkipBuildAuthKeyCheck 1
setkey "$WORLD" Network.EnterEncryptedModeRegionGroup 8
setkey "$WORLD" Realm.CfgContentSetID 137
setkey "$WORLD" Realm.SuperDistrictID 2
setkey "$WORLD" Realm.AlsoAcceptBuilds "\"$ALSO_ACCEPT_BUILDS\""
setkey "$WORLD" Updates.EnableDatabases 15
setkey "$WORLD" Updates.AutoSetup 1
setkey "$WORLD" mmap.enablePathFinding 1          # the bots cannot walk without mmaps
setkey "$WORLD" Logger.sql.sql 5,DBErrors         # ~1M harmless DB warnings per start go to DBErrors.log only
setkey "$WORLD" SOAP.Enabled 0                    # Yu'lon talks to the console (/opt/forever/yulon/console.sh)
setkey "$WORLD" Ra.Enable 0
setkey "$WORLD" PlayerSave.Stats.MinLevel 1

# The build's own module confs (playerbot.conf, zz-forever-bots.conf, zz-forever-lfg.conf, ...), once each
for f in "$DIST"/worldserver.conf.d/*; do
  [ -e "$f" ] || continue
  b=$(basename "$f"); t="$ETC/worldserver.conf.d/${b%.dist}"
  [ -f "$t" ] || cp "$f" "$t"
done

cat > "$ETC/worldserver.conf.d/zz-zz-yulon.conf" <<'EOF'
[worldserver]
# Yu'lon's realm settings: rewritten at every start. Put your own overrides in a file that sorts after this one
# (for example zz-zz-zz-mine.conf): worldserver reads this folder in name order and the last value wins.
# World bots on and their roster seeded, like Karrz's repack; no LLM chat.
Playerbot.Enable = 1
Playerbot.World.Enable = 1
Playerbot.World.SeedRoster = 1
Playerbot.ChatModel.Enable = 0
# Play like official WoW Forever: mob health from the curve fit to sniffed official Forever creatures, and the
# official kill XP for mobs below the player's level (both default off in the core).
Classic.ForeverCreatureHealth = 1
Classic.ForeverKillXp = 1
EOF
if [ -n "${BOT_SETTINGS:-}" ]; then
  printf '# Bot caps for this computer (Yu'"'"'lon)\n' >> "$ETC/worldserver.conf.d/zz-zz-yulon.conf"
  printf '%s\n' "$BOT_SETTINGS" | tr ';' '\n' | sed 's/^ *//' >> "$ETC/worldserver.conf.d/zz-zz-yulon.conf"
fi
say "configuration ready in /srv/etc"
