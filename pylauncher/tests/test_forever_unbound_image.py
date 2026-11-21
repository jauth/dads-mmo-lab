"""WoW Forever Unbound's own server image: its recipe, its core patches and its release.

The image is built by the maintainer from `catalog/installers/wow-forever-unbound/image/` and
`patches/`, then published and pinned by digest (design D1, D5, D6). Nothing here builds it. These
tests pin what it is built from, byte for byte, so that a drifted patch, a re-copied script or a
WoW Forever release bump without a rebuild fails here and not in a player's game.
"""

from __future__ import annotations

import hashlib
import re

import pytest

from yulon import forever_unbound_sql as mentor_sql
from yulon import resources
from yulon.catalog.catalog import SingleEntry, load_catalog
from yulon.catalog.stack_install import stack_of

ENTRY_DIR = resources.installers_dir() / "wow-forever-unbound"
IMAGE_DIR = ENTRY_DIR / "image"
PATCH_DIR = ENTRY_DIR / "patches"
DOCKERFILE = (IMAGE_DIR / "Dockerfile").read_text(encoding="utf-8")
CATALOG = load_catalog()
FOREVER: SingleEntry = CATALOG.get_single("wow-forever")
UNBOUND: SingleEntry = CATALOG.get_single("wow-forever-unbound")

# name -> sha256, in the order the Dockerfile applies them (name order).
# 0001 is forever-bots' own patch, a byte copy of its /opt/forever/src/build/patches/ file: it has
# CRLF lines because the CascLib files it changes are CRLF, which is why `.gitattributes` marks the
# folder -text. 0002 is Yu'lon's: the Mentor script, and one line in the custom script loader.
PATCHES: dict[str, str] = {
    "0001-casclib-local-storage-read-only.patch": "74903cbda80c30afaa3dd3665f0bc8ef3cdd7aebcddbf8fd4d7198084308f151",  # noqa: E501
    "0002-yulon-mentor-script.patch": "f0dea03bcda9e6fb464bcfbb2d205dd2b816cf4ceb6459bfa2425743ce4a798c",  # noqa: E501
}

# Byte copies out of ghcr.io/dadsmmolab/forever-bots@sha256:ebef1a2e... (the change's notes.md,
# task 1.2): the image's realm scripts and its build ignore file, unchanged.
VENDORED: dict[str, str] = {
    "Dockerfile.dockerignore": "8af73c3cf6b6e2b07d0d6e1f724be31e5c53d71c1a84ad88e3f2ec34d3500b1b",
    "yulon/certs.sh": "8da2c41678c45a80aa675f3f3c0898945c772cc1b379421e834ddfefa82f38f0",
    "yulon/common.sh": "b89dbc9f528f26b87d5511667201b72adc5968dce2b48dfba76c51ee424a0555",
    "yulon/configure.sh": "22f624789df4735027f65bec917eda3c5f9e96444bfacc0f7035b40fbf10fbd0",
    "yulon/console.sh": "b27005119d70a2c32ab1d163346cabb42731bcc15a82d3828d3fb40ec2bf16e3",
    "yulon/db-init.sh": "5fb00f19647bca596670df51968a6da7e0629b3d7903eb90f8b37c8ba8dd7a23",
    "yulon/extract.sh": "b157a8797c898871ee78f7612ed3c43ff2711b0776fb57e4da5ae2b45a666fa8",
    "yulon/tdb.sh": "fab32e38cb1cdff24396440c052bbcb243e0b165a70827537018d749de0868ab",
    "yulon/world.sh": "4348ffa046482a3d84f90352cf807faf5c5f28d744622e1ff6571dfba7aabc0d",
}


def _arg(name: str) -> str:
    """The default of `ARG <name>=...` in the Dockerfile."""
    found: list[str] = re.findall(rf"^ARG {name}=(\S+)$", DOCKERFILE, re.M)
    assert len(found) == 1, f"one ARG {name}"
    return found[0]


# -- the patches -------------------------------------------------------------------------------


def test_the_patch_folder_holds_exactly_the_patches_in_order_and_their_reasons() -> None:
    names = sorted(p.name for p in PATCH_DIR.glob("*.patch"))
    assert names == list(PATCHES)
    assert sorted(p.name for p in PATCH_DIR.iterdir()) == [*PATCHES, "README.txt"]


@pytest.mark.parametrize(("name", "digest"), PATCHES.items())
def test_every_patch_is_shipped_byte_exact(name: str, digest: str) -> None:
    assert hashlib.sha256((PATCH_DIR / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name", PATCHES)
def test_every_patch_has_one_reason_a_player_can_read(name: str) -> None:
    readme = (PATCH_DIR / "README.txt").read_text(encoding="utf-8")
    reasons = [line for line in readme.splitlines() if line.startswith(f"{name}: ")]
    assert len(reasons) == 1, f"{name} needs one '<file>: <reason>' line in patches/README.txt"
    reason = reasons[0].removeprefix(f"{name}: ")
    assert reason[0].isupper() and reason.endswith("."), reason


def test_the_mentor_patch_adds_the_script_the_sql_names_and_touches_nothing_outside_custom() -> (
    None
):
    """The image and the SQL move as a pair: the SQL's ScriptName is the one 0002 registers."""
    patch = (PATCH_DIR / "0002-yulon-mentor-script.patch").read_text(encoding="utf-8")
    assert f"RegisterCreatureAI({mentor_sql.SCRIPT_NAME});" in patch
    touched = re.findall(r"^\+\+\+ b/(\S+)", patch, re.M)
    assert touched == [
        "src/server/scripts/Custom/Yulon/yulon_mentor.cpp",
        "src/server/scripts/Custom/custom_script_loader.cpp",
    ]
    assert "IsBot()" in patch, "a bot is never taught"
    assert patch.index("HasEnoughMoney(price)") < patch.index("ModifyMoney(-int64(price))")
    assert patch.index("ModifyMoney(-int64(price))") < patch.index("LearnSpell(spellId, false)")


# -- the recipe --------------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "digest"), VENDORED.items())
def test_forever_bots_files_are_unchanged_copies(name: str, digest: str) -> None:
    assert hashlib.sha256((IMAGE_DIR / name).read_bytes()).hexdigest() == digest


def test_the_dockerfile_applies_every_patch_strictly_before_building() -> None:
    source = DOCKERFILE.index("FROM ubuntu:24.04 AS source")
    build = DOCKERFILE.index("FROM ubuntu:24.04 AS build")
    apply = DOCKERFILE.index("patch -p1 --forward --batch -d /src")
    assert source < apply < build, "patches are applied in the source stage, before cmake"
    assert "COPY --from=patches *.patch /patches/" in DOCKERFILE
    assert "for p in /patches/*.patch" in DOCKERFILE, "in name order"
    assert "exit 1" in DOCKERFILE[apply:build], "a patch that fails stops the build"
    assert "COPY --from=source /src /src" in DOCKERFILE[build:]


def test_the_image_carries_its_gpl_source_and_says_where_it_came_from() -> None:
    assert (
        "COPY --from=yulon Dockerfile Dockerfile.dockerignore README.md /opt/forever/src/build/"
        in (DOCKERFILE)
    )
    assert "COPY --from=patches / /opt/forever/src/build/patches/" in DOCKERFILE
    assert 'org.opencontainers.image.licenses="GPL-2.0-only"' in DOCKERFILE
    assert 'org.opencontainers.image.source="${SOURCE_URL}"' in DOCKERFILE
    assert 'org.opencontainers.image.revision="${SOURCE_SHA256}"' in DOCKERFILE
    assert 'org.opencontainers.image.title="forever-unbound"' in DOCKERFILE
    assert 'org.opencontainers.image.version="${SOURCE_VERSION}-${YULON_BUILD}"' in DOCKERFILE
    assert re.fullmatch(r"u\d+", _arg("YULON_BUILD"))
    for name in ("advocaite", "Karrz", "TrinityCore", "DaddyCool"):
        assert name in DOCKERFILE


# -- one release with WoW Forever ---------------------------------------------------------------


def test_it_is_built_from_the_release_wow_forevers_image_is() -> None:
    """A WoW Forever bump fails here until this image is rebuilt from the new release (D5)."""
    version = _arg("SOURCE_VERSION")
    label = stack_of(FOREVER).image("server").label
    assert label.endswith(
        f"release {version}"
    ), f"WoW Forever runs {label!r}, but WoW Forever Unbound's image is built from {version}"
    zip_name = f"wow-forever-source-{version}.zip"
    assert _arg("SOURCE_URL") == (
        f"https://github.com/Karrz1/Karrz-playerbots-wow-forever/releases/download/v{version}/{zip_name}"
    )
    assert re.fullmatch(r"[0-9a-f]{64}", _arg("SOURCE_SHA256"))
    assert UNBOUND.emulator.sources == FOREVER.emulator.sources
