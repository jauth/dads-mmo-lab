#!/usr/bin/env bash
# Starts worldserver with its console on a named pipe, so Yu'lon can type console commands into it with
# `docker exec <world container> /opt/forever/yulon/console.sh "<command>"` (no terminal needed); replies go to
# the container log. worldserver stops at end of input on a pipe (CliRunnable.cpp: feof -> World::StopNow),
# so a writer that never writes holds the pipe open for the server's whole life.
source /opt/forever/yulon/common.sh
P=/run/yulon/console
mkdir -p /run/yulon
rm -f "$P"
mkfifo "$P"
sleep infinity > "$P" &
cd /srv/tdb
exec /opt/forever/bin/worldserver -c /srv/etc/worldserver.conf --config-dir /srv/etc/worldserver.conf.d < "$P"
