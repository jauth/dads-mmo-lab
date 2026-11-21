#!/usr/bin/env bash
# This computer's own CA and the trinity.actual.battle.net certificate bnetserver serves (/srv/certs), made once.
# The CA is name-constrained to actual.battle.net, so trusting it lets it vouch for those names and nothing else.
# Its key never leaves this folder; the player's computer trusts ca.pem (Yu'lon's one administrator prompt).
source /opt/forever/yulon/common.sh
C=/srv/certs
mkdir -p "$C"
if [ -f "$C/chain.pem" ] && [ -f "$C/server.key" ] && [ -f "$C/ca.pem" ]; then
  say "certificates ready"; exit 0
fi
NAME=${CA_NAME:-Yulon WoW Forever Local CA}
tmp=$(mktemp -d)
cat > "$tmp/ca.cnf" <<EOF
[req]
distinguished_name=dn
x509_extensions=ca
prompt=no
[dn]
CN=${NAME}
[ca]
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
nameConstraints=critical,permitted;DNS:actual.battle.net
EOF
printf '[req]\ndistinguished_name=dn\nprompt=no\n[dn]\nCN=trinity.actual.battle.net\n' > "$tmp/server.cnf"
printf 'subjectAltName=DNS:trinity.actual.battle.net\nextendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid:always\n' > "$tmp/leaf.ext"
openssl req -x509 -newkey rsa:3072 -nodes -keyout "$tmp/ca.key" -out "$tmp/ca.pem" -days 3650 -config "$tmp/ca.cnf" 2>/dev/null
openssl req -new -newkey rsa:2048 -nodes -keyout "$tmp/server.key" -out "$tmp/server.csr" -config "$tmp/server.cnf" 2>/dev/null
openssl x509 -req -in "$tmp/server.csr" -CA "$tmp/ca.pem" -CAkey "$tmp/ca.key" -CAcreateserial -out "$tmp/server.pem" \
  -days 825 -extfile "$tmp/leaf.ext" 2>/dev/null
cat "$tmp/server.pem" "$tmp/ca.pem" > "$tmp/chain.pem"
openssl verify -CAfile "$tmp/ca.pem" "$tmp/server.pem" >/dev/null
cp "$tmp/ca.key" "$tmp/ca.pem" "$tmp/server.key" "$tmp/server.pem" "$tmp/chain.pem" "$C/"
chmod 600 "$C/ca.key" "$C/server.key"
rm -rf "$tmp"
say "made the CA \"$NAME\" and the trinity.actual.battle.net certificate"
