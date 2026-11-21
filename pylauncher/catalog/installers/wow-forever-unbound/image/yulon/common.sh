# Shared by the Yu'lon scripts in /opt/forever/yulon. Sourced, never run.
# Paths inside the containers of a Yu'lon WoW Forever install:
#   /srv/etc     bnetserver.conf, worldserver.conf, worldserver.conf.d/   (the install folder's etc/)
#   /srv/logs    Server.log, Bnet.log, Playerbot.log, DBErrors.log       (the install folder's logs/)
#   /srv/certs   this computer's CA + the trinity.actual.battle.net leaf (the install folder's certs/)
#   /srv/data    dbc gt maps vmaps mmaps Cameras, extracted from the player's own client (a volume)
#   /srv/tdb     the world and hotfixes database release worldserver imports on its first start (a volume)
#   /srv/downloads  the TDB release archive Yu'lon downloaded and checked (the install folder's downloads/, read-only)
#   /opt/forever/src/sql  the server's own SQL updates (baked into the image)
set -euo pipefail

say() { printf '[yulon] %s\n' "$*"; }

# setkey <file> <key> <value>: replace "key = ..." or append it (keys are TrinityCore config names)
setkey() {
  local file=$1 key=$2 value=$3 esc
  esc=$(printf '%s' "$key" | sed 's/[.[\*^$/]/\\&/g')
  if grep -qE "^${esc}[[:space:]]*=" "$file"; then
    sed -i -E "s|^${esc}[[:space:]]*=.*|${key} = ${value//|/\\|}|" "$file"
  else
    printf '\n%s = %s\n' "$key" "$value" >> "$file"
  fi
}

need() { [ -n "${!1:-}" ] || { say "missing environment variable $1"; exit 2; }; }
