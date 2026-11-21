#!/usr/bin/env bash
# Makes the database user and the four empty databases worldserver fills, and the bots' shared database.
# Runs at every start (compose service "database-init", once the database is healthy); every step is idempotent.
source /opt/forever/yulon/common.sh
need MYSQL_ROOT_PASSWORD
need DB_PASSWORD
DB_HOST=${DB_HOST:-database}
q() { mysql -h "$DB_HOST" -uroot -p"$MYSQL_ROOT_PASSWORD" --protocol=tcp "$@"; }
for i in $(seq 1 60); do q -e 'SELECT 1' >/dev/null 2>&1 && break; sleep 2; done
q -e 'SELECT 1' >/dev/null
q <<SQL
CREATE USER IF NOT EXISTS 'trinity'@'%' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER 'trinity'@'%' IDENTIFIED BY '${DB_PASSWORD}';
CREATE DATABASE IF NOT EXISTS auth DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS characters DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS world DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS hotfixes DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON auth.* TO 'trinity'@'%';
GRANT ALL PRIVILEGES ON characters.* TO 'trinity'@'%';
GRANT ALL PRIVILEGES ON world.* TO 'trinity'@'%';
GRANT ALL PRIVILEGES ON hotfixes.* TO 'trinity'@'%';
GRANT ALL PRIVILEGES ON playerbot.* TO 'trinity'@'%';
-- The world release creates 3 helper views with DEFINER=trinity@localhost: that user must exist, and the importing
-- user needs SET_USER_ID to name another definer (else error 1227 and an empty world).
CREATE USER IF NOT EXISTS 'trinity'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON world.* TO 'trinity'@'localhost';
GRANT SET_USER_ID ON *.* TO 'trinity'@'%';
FLUSH PRIVILEGES;
SQL
if ! q -N -e "SHOW DATABASES LIKE 'playerbot'" | grep -q playerbot; then
  say "importing the bots' shared database"
  q < /opt/forever/src/sql/playerbot_shared/playerbot_shared_schema.sql
  q playerbot < /opt/forever/src/sql/playerbot_shared/playerbot_shared_data.sql
fi
say "database ready"
