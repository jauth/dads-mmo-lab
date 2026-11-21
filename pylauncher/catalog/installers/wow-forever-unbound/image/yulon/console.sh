#!/usr/bin/env bash
# Types one line into the running worldserver's console (see world.sh). The reply is printed in the container log.
#   docker exec <world container> /opt/forever/yulon/console.sh "bnetaccount create name@example.local password"
set -euo pipefail
P=/run/yulon/console
[ -p "$P" ] || { echo "the world server's console pipe is not there: is it running?" >&2; exit 2; }
printf '%s\n' "$*" > "$P"
