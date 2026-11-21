# WoW Forever Unbound: WoW Forever (Classic 1.60.1) server with Karrz's PlayerbotV2 bots and Yu'lon's Forever Unbound
# core patches, built from Karrz's release source on Ubuntu 24.04 (the toolchain doc/LinuxServerSetup.md was tested
# with: GCC 13, Boost 1.83, MySQL 8.0). This is forever-bots' recipe (/opt/forever/src/build/Dockerfile in that image)
# with one change of substance: the patches are applied HERE, in order, instead of to the tree by hand beforehand.
# Build context = the unpacked release source (wow-forever-source-<version>.zip from
# github.com/Karrz1/Karrz-playerbots-wow-forever/releases); this file is passed with -f, this folder is the named
# context "yulon" and the entry's patches/ folder is the named context "patches" (README.md has the full command):
#   docker build -f image/Dockerfile --build-context yulon=image --build-context patches=patches \
#     -t ghcr.io/jauth/forever-unbound:0.1.36-u1 src-0.1.36
# `--target source` stops after the patches are applied: a quick check that every patch still applies.

# The release source with Yu'lon's patches applied, strictly: a hunk that does not apply stops the build.
FROM ubuntu:24.04 AS source
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends patch \
 && rm -rf /var/lib/apt/lists/*
COPY . /src
COPY --from=patches *.patch /patches/
RUN for p in /patches/*.patch; do \
      echo "Applying $(basename "$p")"; \
      patch -p1 --forward --batch -d /src < "$p" || { echo "PATCH FAILED: $(basename "$p")"; exit 1; }; \
    done

FROM ubuntu:24.04 AS build
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
      build-essential g++-13 cmake make git ca-certificates libboost-all-dev libreadline-dev libbz2-dev \
      libssl-dev libmysqlclient-dev libncurses-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY --from=source /src /src
ARG JOBS=4
RUN cmake -S /src -B /build -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/opt/forever \
      -DSERVERS=1 -DTOOLS=1 -DSCRIPTS=static -DBUILD_PLAYERBOT_V2=1 -DWITH_WARNINGS=0 \
 && cmake --build /build -j${JOBS} \
 && cmake --install /build \
 && mkdir -p /opt/forever/sql \
 && cp -r /src/sql/playerbot_shared /src/sql/playerbot_v2 /opt/forever/sql/ 2>/dev/null || true \
 && cp -r /src/src/modules/PlayerbotV2/Addon /opt/forever/addon 2>/dev/null || true
# The server's own sql/ (base, updates, custom, playerbot; sql/old is not in the context), so a realm needs no source
# checkout: worldserver.conf SourceDirectory = /opt/forever/src.
RUN mkdir -p /opt/forever/src && cp -r /src/sql /opt/forever/src/sql

FROM ubuntu:24.04
# 7zip: unpacks the TDB release (TDB_full_forever_*.7z) inside the container, so the host needs no 7-Zip.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
      libboost-filesystem1.83.0 libboost-program-options1.83.0 libboost-iostreams1.83.0 libboost-regex1.83.0 \
      libboost-locale1.83.0 libboost-thread1.83.0 libreadline8t64 libbz2-1.0 libssl3t64 libmysqlclient21 zlib1g \
      libncursesw6 mysql-client openssl ca-certificates 7zip \
 && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/forever /opt/forever
# GPL-2 corresponding source = the release's source zip (SOURCE_URL, sha256 SOURCE_SHA256) plus these patches;
# this Dockerfile builds it.
COPY --from=yulon Dockerfile Dockerfile.dockerignore README.md /opt/forever/src/build/
COPY --from=patches / /opt/forever/src/build/patches/
# Yu'lon's realm scripts (configure, database init, certificates, TDB unpack, map extraction, console on a pipe).
COPY --from=yulon yulon/ /opt/forever/yulon/
RUN chmod 755 /opt/forever/yulon/*.sh && sed -i 's/\r$//' /opt/forever/yulon/*.sh
ARG SOURCE_VERSION=0.1.36
ARG SOURCE_URL=https://github.com/Karrz1/Karrz-playerbots-wow-forever/releases/download/v0.1.36/wow-forever-source-0.1.36.zip
ARG SOURCE_SHA256=1e92c3d84833b5500695255a83e92971d167fe5c906393ad2d973a086f4f522d
ARG YULON_BUILD=u1
LABEL org.opencontainers.image.title="forever-unbound" \
      org.opencontainers.image.version="${SOURCE_VERSION}-${YULON_BUILD}" \
      org.opencontainers.image.description="WoW Forever Unbound: WoW Forever (Classic 1.60.1, realm build 70707) server with Karrz's PlayerbotV2 bots, release ${SOURCE_VERSION}, and Yu'lon's Forever Unbound core patches: built from ${SOURCE_URL} (sha256 ${SOURCE_SHA256}) + the patches in /opt/forever/src/build/patches, by the Dockerfile beside them. Credits: advocaite (Forever core), Karrz (PlayerbotV2), TrinityCore; the Unbound design is DaddyCool's (Wrath Unbound)." \
      org.opencontainers.image.url="https://github.com/Karrz1/Karrz-playerbots-wow-forever/releases/tag/v${SOURCE_VERSION}" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${SOURCE_SHA256}" \
      org.opencontainers.image.licenses="GPL-2.0-only"
# Fail the build if any binary is missing a shared library.
RUN for f in /opt/forever/bin/*; do ldd "$f" 2>/dev/null | grep 'not found' && echo "MISSING LIBS: $f" && exit 1; done; true
WORKDIR /opt/forever/bin
