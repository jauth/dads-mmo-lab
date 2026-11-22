"""The WDC5 reader, on a small table built here byte by byte (no client file is needed)."""

from __future__ import annotations

import struct

import pytest

from yulon.wdc5 import (
    HEADER,
    SECTION,
    STORAGE,
    STORAGE_BITPACKED,
    STORAGE_BITPACKED_SIGNED,
    STORAGE_COMMON,
    STORAGE_PALLET,
    STORAGE_PLAIN,
    Wdc5Error,
    Wdc5Table,
)

RECORD_SIZE = 8
NAMES = (b"Frostbolt\0", b"Moonfire\0")
PALLET = (100, 200, 300)
COMMON_DEFAULT = 7


def _record(index: int, name_value: int, packed: int, pallet_index: int, signed: int) -> bytes:
    bits = name_value | (packed << 32) | (pallet_index << 40) | ((signed & 0x3F) << 42)
    return bits.to_bytes(RECORD_SIZE, "little")


def _table(*, flags: int = 0x4, encrypted_first: bool = False, key: int = 0) -> bytes:
    """Two rows (ids 10 and 11), a copy (12 of 10), parents 500 and 501, and five columns.

    Column 0 is a plain string offset, 1 bitpacked (8 bits), 2 a pallet index (2 bits), 3 common
    data (row 11 differs from the default), 4 signed bitpacked (6 bits).
    """
    storages = [
        (0, 32, 0, STORAGE_PLAIN, 0, 0, 0),
        (32, 8, 0, STORAGE_BITPACKED, 0, 8, 0),
        (40, 2, 12, STORAGE_PALLET, 40, 2, 0),
        (0, 0, 8, STORAGE_COMMON, COMMON_DEFAULT, 0, 0),
        (42, 6, 0, STORAGE_BITPACKED_SIGNED, 42, 6, 0),
    ]
    fields = b"".join(struct.pack("<hH", 0, s[0] // 8) for s in storages)
    storage_block = b"".join(STORAGE.pack(*s) for s in storages)
    pallet = struct.pack("<3I", *PALLET)
    common = struct.pack("<II", 11, 99)
    strings = b"".join(NAMES)
    total = 2
    # A string value counts from the field's own place, as if all records came before the strings.
    name0 = 0 + (total - 0) * RECORD_SIZE
    name1 = len(NAMES[0]) + (total - 1) * RECORD_SIZE
    records = _record(0, name0, 42, 1, -3) + _record(1, name1, 255, 2, 5)
    ids = struct.pack("<2I", 10, 11)
    copies = struct.pack("<II", 12, 10)
    relationship = struct.pack("<3I", 2, 500, 501) + struct.pack("<4I", 500, 0, 501, 1)
    sections = 2 if encrypted_first else 1
    data_start = HEADER.size + sections * SECTION.size + len(fields) + len(storage_block)
    file_offset = data_start + len(pallet) + len(common)
    section = SECTION.pack(key, file_offset, 2, len(strings), 0, len(ids), len(relationship), 0, 1)
    headers = section
    if encrypted_first:
        # An encrypted section with no records, placed before the real one.
        headers = SECTION.pack(0xABCD, file_offset, 0, 0, 0, 0, 0, 0, 0) + section
    header = HEADER.pack(
        b"WDC5", 5, b"\0" * 128, 2, 5, RECORD_SIZE, len(strings), 0, 0, 10, 11, 0,
        flags, 0, 5, 0, 0, len(storage_block), len(common), len(pallet), sections,
    )  # fmt: skip
    body = records + strings + ids + copies + relationship
    return header + headers + fields + storage_block + pallet + common + body


def test_reads_every_kind_of_field() -> None:
    table = Wdc5Table(_table())
    first, second = table.rows[10], table.rows[11]
    assert (first.string(0), second.string(0)) == ("Frostbolt", "Moonfire")
    assert (first.value(1), second.value(1)) == (42, 255)
    assert (first.value(2), second.value(2)) == (PALLET[1], PALLET[2])
    assert (first.value(3), second.value(3)) == (COMMON_DEFAULT, 99)
    assert (first.signed(4), second.signed(4)) == (-3, 5)


def test_ids_parents_and_copies() -> None:
    table = Wdc5Table(_table())
    assert sorted(table.rows) == [10, 11, 12]
    assert (table.rows[10].parent, table.rows[11].parent) == (500, 501)
    copy = table.rows[12]
    assert copy.parent == 500
    assert copy.string(0) == "Frostbolt"
    assert copy.value(1) == 42


def test_skips_an_encrypted_section() -> None:
    table = Wdc5Table(_table(encrypted_first=True))
    assert table.rows[11].string(0) == "Moonfire"


def test_reads_a_decrypted_section() -> None:
    """The extractor keeps a decrypted section's key hash; its rows are real and are read."""
    table = Wdc5Table(_table(key=0x5452494E49545900))
    assert table.rows[11].string(0) == "Moonfire"


def test_a_zero_string_offset_is_an_empty_string() -> None:
    table = Wdc5Table(_table())
    row = table.rows[10]
    assert table.string_at(row._record, 0, 0) == ""


def test_refuses_what_it_cannot_read() -> None:
    with pytest.raises(Wdc5Error):
        Wdc5Table(b"WDC3" + bytes(HEADER.size))
    with pytest.raises(Wdc5Error):
        Wdc5Table(_table(flags=0x5))
