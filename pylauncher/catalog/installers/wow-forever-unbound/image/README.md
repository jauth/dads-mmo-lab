# WoW Forever Unbound server image

The server image WoW Forever Unbound runs: `ghcr.io/jauth/forever-unbound`, pinned by digest in
`pylauncher/yulon/catalog/catalog.json`. It is WoW Forever's server, ForeverCore with Karrz's
PlayerbotV2 bots, built from the same release source, plus Yu'lon's Forever Unbound core patches.

## What is here

| Path | What it is |
|---|---|
| `image/Dockerfile` | The recipe. It is `forever-bots`' own recipe (`/opt/forever/src/build/Dockerfile` in that image), with the patches applied by the build itself in a `source` stage, and Unbound labels. |
| `image/Dockerfile.dockerignore` | `forever-bots`' ignore file, unchanged (keeps `.git`, `build`, `out` and `sql/old` out of the context). |
| `image/yulon/*.sh` | Yu'lon's realm scripts, byte copies of `forever-bots`' `/opt/forever/yulon/`. |
| `../patches/*.patch` | The core patches, applied in name order. `../patches/README.txt` gives one reason for each. |

`pylauncher/tests/test_forever_unbound_image.py` pins every file here by sha256, the patch order,
and that the release matches WoW Forever's own image.

## GPL-2 source

The image is GPL-2.0-only. Its corresponding source is the release source archive named in its
labels (`org.opencontainers.image.source`, sha256 in `org.opencontainers.image.revision`), plus
the patches and this Dockerfile, which the image carries in `/opt/forever/src/build/`. To see them:

```sh
docker run --rm --entrypoint ls ghcr.io/jauth/forever-unbound@sha256:<digest> -R /opt/forever/src/build
```

## Build

On a Linux or Docker Desktop computer with about 30 GB free. It takes about an hour with 6 jobs.

```sh
# 1. The release source, checked against the sha256 in the Dockerfile's SOURCE_SHA256.
curl -LO https://github.com/Karrz1/Karrz-playerbots-wow-forever/releases/download/v0.1.36/wow-forever-source-0.1.36.zip
sha256sum wow-forever-source-0.1.36.zip   # 1e92c3d84833b5500695255a83e92971d167fe5c906393ad2d973a086f4f522d
unzip -q wow-forever-source-0.1.36.zip -d src-0.1.36

# 2. Quick check: do all the patches still apply? (seconds)
docker build -f image/Dockerfile --build-context yulon=image --build-context patches=patches \
  --target source src-0.1.36/wow-forever-source-0.1.36

# 3. The image. Run from pylauncher/catalog/installers/wow-forever-unbound/.
docker build -f image/Dockerfile --build-context yulon=image --build-context patches=patches \
  --build-arg JOBS=6 -t ghcr.io/jauth/forever-unbound:0.1.36-u1 src-0.1.36/wow-forever-source-0.1.36
```

Don't apply patches by hand, and never build from a tree that already has them applied: `patch
--forward` refuses a patch that is already there, and the build stops.

## Smoke test before publishing

Put the local tag in place of the `image:` ref in an Unbound install's `docker-compose.yml`, and
start the install with `docker compose up -d` in its folder. Then check that:
- the world log reaches `(worldserver-daemon) ready` with no unknown-ScriptName error for
  `npc_yulon_mentor`
- Play logs in
- the Mentor charges and teaches
- a bot party plays normally

## Publish (owner's go-ahead only)

Publishing makes a public package. Do it only when the owner says so.

```sh
docker push ghcr.io/jauth/forever-unbound:0.1.36-u1     # prints the digest
# On GitHub: Packages > forever-unbound > Package settings > Change visibility > Public.
docker logout ghcr.io && docker pull ghcr.io/jauth/forever-unbound@sha256:<digest>   # works signed out
```

Then put `ghcr.io/jauth/forever-unbound@sha256:<digest>` in `catalog.json`, as the `server`
image of `wow-forever-unbound`.

## A new ForeverCore release

When WoW Forever's image moves to a new release, `test_forever_unbound_image.py` fails until this
image follows:
1. Copy the new `forever-bots` recipe and scripts out of its image (`docker create` + `docker cp`).
2. Re-apply this Dockerfile's `source` stage and labels.
3. Set `SOURCE_VERSION`, `SOURCE_URL` and `SOURCE_SHA256`, and reset `YULON_BUILD` to `u1`.
4. Run the quick check, and refresh any patch that no longer applies.
5. Build, smoke-test and publish again.

Raise `YULON_BUILD` (`u2`, `u3`, …) when only Yu'lon's patches change.

## Credits

advocaite (the Forever core), Karrz (PlayerbotV2 bots and the 0.1.36 release), and TrinityCore.
The Unbound design (a Mentor who teaches other classes' spells) is DaddyCool's, from Wrath Unbound.
