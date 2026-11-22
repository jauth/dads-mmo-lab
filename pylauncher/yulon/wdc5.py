"""Read a client table in the WDC5 format: its rows by id, each as numbers and strings.

The game client keeps its tables (spells, names, power costs...) in `.db2` files. The server's
data volume holds the files extracted from the player's own client. Yu'lon reads a few of them
only in developer tools (the Forever Unbound curation tool), never in the app, and never ships one.

This reader covers what the client's spell tables use: plain, bitpacked, common-data and pallet
fields (plain and array), the string block, the id list, the copy table and the relationship map
(the parent id that tables such as SpellPower keep outside the record). An encrypted section is
read when the extractor decrypted it and skipped when its records are still zeros. Tables with
variable-size records (header flag 1) are refused.

Columns are read by their index in the file. The file does not name them; the caller knows, and
checks itself against rows whose values it already knows.

The layout follows the community's public WDC5 notes (wowdev.wiki).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"WDC5"
HEADER = struct.Struct("<4sI128s9IHH7I")
"""magic, version, schema text, nine counts and hashes, flags, id index, seven sizes."""
SECTION = struct.Struct("<Q8I")
FIELD = struct.Struct("<hH")
STORAGE = struct.Struct("<HHIIIII")

FLAG_VARIABLE_RECORDS = 0x1

STORAGE_PLAIN = 0
STORAGE_BITPACKED = 1
STORAGE_COMMON = 2
STORAGE_PALLET = 3
STORAGE_PALLET_ARRAY = 4
STORAGE_BITPACKED_SIGNED = 5


class Wdc5Error(ValueError):
    """The file is not a WDC5 table this reader can read."""


@dataclass(frozen=True, slots=True)
class _Column:
    offset_bits: int
    size_bits: int
    storage: int
    value1: int
    value2: int
    value3: int
    element_bits: int
    pallet_start: int
    common_start: int
    common_size: int


@dataclass(frozen=True, slots=True)
class Row:
    """One row: its id, its parent id (0 when the table has none), and where its bytes are."""

    row_id: int
    parent: int
    _table: Wdc5Table
    _record: int

    def values(self, column: int) -> tuple[int, ...]:
        """Column `column`'s values as unsigned 32-bit numbers (one, or several for an array)."""
        return self._table.column_values(self._record, self.row_id, column)

    def value(self, column: int) -> int:
        """Column `column`'s first value."""
        return self.values(column)[0]

    def signed(self, column: int) -> int:
        """Column `column`'s first value read as a signed 32-bit number."""
        value = self.value(column)
        return value - (1 << 32) if value & 0x80000000 else value

    def string(self, column: int) -> str:
        """Column `column` read as a string from the string block."""
        return self._table.string_at(self._record, column, self.value(column))


class Wdc5Table:
    """A WDC5 file's rows, by id."""

    def __init__(self, data: bytes) -> None:
        if len(data) < HEADER.size or data[:4] != MAGIC:
            raise Wdc5Error("not a WDC5 file")
        (
            _magic,
            _version,
            _schema,
            self.record_count,
            self.field_count,
            self.record_size,
            _string_size,
            self.table_hash,
            self.layout_hash,
            _min_id,
            _max_id,
            _locale,
            flags,
            self.id_index,
            _total_fields,
            _bitpacked_offset,
            _lookup_columns,
            storage_size,
            common_size,
            pallet_size,
            section_count,
        ) = HEADER.unpack_from(data, 0)
        if flags & FLAG_VARIABLE_RECORDS:
            raise Wdc5Error("variable-size records are not supported")
        self._data = data
        offset = HEADER.size
        sections = [
            SECTION.unpack_from(data, offset + i * SECTION.size) for i in range(section_count)
        ]
        offset += section_count * SECTION.size
        sizes = [FIELD.unpack_from(data, offset + i * FIELD.size) for i in range(self.field_count)]
        offset += self.field_count * FIELD.size
        storages = [
            STORAGE.unpack_from(data, offset + i * STORAGE.size)
            for i in range(storage_size // STORAGE.size)
        ]
        offset += storage_size
        pallet_base = offset
        common_base = pallet_base + pallet_size
        self._columns = self._read_columns(sizes, storages, pallet_base, common_base)

        self.rows: dict[int, Row] = {}
        self._record_starts: list[int] = []
        self._string_starts: list[tuple[int, int]] = []
        """Per section, in order: its string block's start in the file, and its size."""
        global_index = 0
        copies: list[tuple[int, int]] = []
        for (
            key_hash,
            file_offset,
            count,
            string_size,
            _end,
            id_size,
            rel_size,
            _omap,
            copy_count,
        ) in sections:
            records = file_offset
            strings = records + count * self.record_size
            self._string_starts.append((strings, string_size))
            if key_hash and not any(data[records:strings]):
                # An encrypted section the extractor could not decrypt: its records are zeros.
                # (A decrypted one keeps its key hash and holds real rows.) Its records and
                # strings still count toward the string offsets of later sections.
                self._record_starts.extend([records] * count)
                global_index += count
                continue
            cursor = strings + string_size
            ids = list(struct.unpack_from(f"<{id_size // 4}I", data, cursor)) if id_size else []
            cursor += id_size
            for i in range(copy_count):
                copies.append(struct.unpack_from("<II", data, cursor + i * 8))
            cursor += copy_count * 8
            parents: dict[int, int] = {}
            if rel_size:
                entries, _rel_min, _rel_max = struct.unpack_from("<3I", data, cursor)
                for i in range(entries):
                    foreign, index = struct.unpack_from("<II", data, cursor + 12 + i * 8)
                    parents[index] = foreign
            for i in range(count):
                start = records + i * self.record_size
                self._record_starts.append(start)
                record = global_index + i
                row_id = ids[i] if ids else self._plain_id(record)
                self.rows[row_id] = Row(row_id, parents.get(i, 0), self, record)
            global_index += count
        self._strings_total_records = global_index
        for new_id, copied_id in copies:
            source = self.rows.get(copied_id)
            if source is not None:
                self.rows[new_id] = Row(new_id, source.parent, self, source._record)

    @staticmethod
    def _read_columns(
        sizes: list[tuple[int, int]],
        storages: list[tuple[int, int, int, int, int, int, int]],
        pallet_base: int,
        common_base: int,
    ) -> list[_Column]:
        columns: list[_Column] = []
        pallet_cursor = pallet_base
        common_cursor = common_base
        for index, (offset_bits, size_bits, extra, storage, v1, v2, v3) in enumerate(storages):
            element_bits = 32 - sizes[index][0] if index < len(sizes) else 32
            pallet_start = pallet_cursor
            common_start = common_cursor
            common_size = 0
            if storage in (STORAGE_PALLET, STORAGE_PALLET_ARRAY):
                pallet_cursor += extra
            elif storage == STORAGE_COMMON:
                common_size = extra
                common_cursor += extra
            columns.append(
                _Column(
                    offset_bits,
                    size_bits,
                    storage,
                    v1,
                    v2,
                    v3,
                    element_bits,
                    pallet_start,
                    common_start,
                    common_size,
                )
            )
        return columns

    @classmethod
    def read(cls, path: Path) -> Wdc5Table:
        """Read the WDC5 file at `path`."""
        return cls(path.read_bytes())

    @property
    def column_count(self) -> int:
        """How many columns each record holds."""
        return len(self._columns)

    def _bits(self, record: int, offset_bits: int, size_bits: int) -> int:
        start = self._record_starts[record] * 8 + offset_bits
        first = start // 8
        last = (start + size_bits + 7) // 8
        number = int.from_bytes(self._data[first:last], "little")
        return (number >> (start % 8)) & ((1 << size_bits) - 1)

    def _plain_id(self, record: int) -> int:
        column = self._columns[self.id_index]
        return self._bits(record, column.offset_bits, column.size_bits)

    def column_values(self, record: int, row_id: int, column_index: int) -> tuple[int, ...]:
        """The values of one column of the record at `record` (row `row_id`)."""
        column = self._columns[column_index]
        if column.storage == STORAGE_PLAIN:
            width = column.element_bits if column.element_bits > 0 else 32
            count = max(1, column.size_bits // width)
            return tuple(
                self._bits(record, column.offset_bits + i * width, width) for i in range(count)
            )
        if column.storage in (STORAGE_BITPACKED, STORAGE_BITPACKED_SIGNED):
            value = self._bits(record, column.offset_bits, column.value2)
            if column.storage == STORAGE_BITPACKED_SIGNED and value >> (column.value2 - 1):
                value = (value - (1 << column.value2)) & 0xFFFFFFFF
            return (value,)
        if column.storage == STORAGE_COMMON:
            return (self._common(column, row_id),)
        if column.storage in (STORAGE_PALLET, STORAGE_PALLET_ARRAY):
            index = self._bits(record, column.offset_bits, column.value2)
            count = column.value3 if column.storage == STORAGE_PALLET_ARRAY else 1
            start = column.pallet_start + index * 4 * count
            return struct.unpack_from(f"<{count}I", self._data, start)
        raise Wdc5Error(f"column {column_index} has unknown storage {column.storage}")

    def _common(self, column: _Column, row_id: int) -> int:
        for i in range(column.common_size // 8):
            entry_id, value = struct.unpack_from("<II", self._data, column.common_start + i * 8)
            if entry_id == row_id:
                return int(value)
        return column.value1

    def string_at(self, record: int, column_index: int, value: int) -> str:
        """The string a string column's `value` points at, for the record at `record`.

        A `value` of 0 is an empty string: the client leaves some records blank.
        """
        if value == 0:
            return ""
        column = self._columns[column_index]
        position = (
            record * self.record_size
            + column.offset_bits // 8
            + value
            - self._strings_total_records * self.record_size
        )
        if position < 0:
            raise Wdc5Error(f"string offset {value} in column {column_index} is before the strings")
        before = 0
        for start, size in self._string_starts:
            if position < before + size:
                local = start + position - before
                end = self._data.index(b"\0", local)
                return self._data[local:end].decode("utf-8")
            before += size
        raise Wdc5Error(f"string offset {value} in column {column_index} is outside the strings")
