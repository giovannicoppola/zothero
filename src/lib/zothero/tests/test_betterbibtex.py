# encoding: utf-8
#
# Copyright (c) 2020 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

"""Unit tests for betterbibtex.py.

Covers all citekey sources `BetterBibTex` understands:

  - the native `citationKey` field in modern Zotero databases (Zotero 7+),
  - the legacy standalone `better-bibtex.sqlite` in both its JSON-blob and
    its `citationkey`-table formats,
  - and the various "no keys available" cases.
"""

from __future__ import print_function, absolute_import

import json
import os
import sqlite3
import tempfile

from zothero.betterbibtex import BetterBibTex


# --------------------------------------------------------------------
# Helpers to build fake databases
# --------------------------------------------------------------------

def _native_conn(keys, with_field=True):
    """In-memory Zotero DB with a native `citationKey` field.

    Args:
        keys: list of ``(libraryID, itemKey, citekey)`` tuples.
        with_field: if ``False``, omit the `citationKey` field from the
            schema, simulating an older Zotero version.
    """
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
        CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT,
                            libraryID INTEGER);
        CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER,
                               valueID INTEGER);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        """
    )
    # A couple of unrelated core fields, plus citationKey (or not).
    conn.execute("INSERT INTO fields VALUES (1, 'title')")
    if with_field:
        conn.execute("INSERT INTO fields VALUES (9, 'citationKey')")

    for i, (lib, key, ck) in enumerate(keys, start=1):
        conn.execute('INSERT INTO items VALUES (?, ?, ?)', (i, key, lib))
        conn.execute('INSERT INTO itemDataValues VALUES (?, ?)', (i, ck))
        conn.execute('INSERT INTO itemData VALUES (?, 9, ?)', (i, i))
    conn.commit()
    return conn


def _legacy_file_blob(keys):
    """Legacy better-bibtex.sqlite in the old JSON-blob format."""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE `better-bibtex` (name TEXT, data TEXT)')
    data = json.dumps({
        'data': [
            {'libraryID': lib, 'itemKey': key, 'citekey': ck}
            for (lib, key, ck) in keys
        ]
    })
    conn.execute(
        "INSERT INTO `better-bibtex` VALUES ('better-bibtex.citekey', ?)",
        (data,),
    )
    conn.commit()
    conn.close()
    return path


def _legacy_file_table(keys):
    """Legacy better-bibtex.sqlite in the newer `citationkey`-table format."""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute(
        'CREATE TABLE citationkey '
        '(libraryID INTEGER, itemKey TEXT, citationKey TEXT)'
    )
    for (lib, key, ck) in keys:
        conn.execute('INSERT INTO citationkey VALUES (?, ?, ?)',
                     (lib, key, ck))
    conn.commit()
    conn.close()
    return path


# --------------------------------------------------------------------
# Native field (modern Zotero / Better BibTeX >= 6.7)
# --------------------------------------------------------------------

def test_native_with_keys():
    """Native citationKey field with keys present."""
    conn = _native_conn([(1, 'ABC', 'foo2020'), (1, 'DEF', 'bar2019')])
    bbt = BetterBibTex(conn)
    assert bbt.exists
    assert bbt.citekey('1_ABC') == 'foo2020'
    assert bbt.citekey('1_DEF') == 'bar2019'
    assert bbt.citekey('1_MISSING') is None


def test_native_field_but_no_keys():
    """Native field present but no item has a key (e.g. Zotero 7, no BBT)."""
    conn = _native_conn([])
    bbt = BetterBibTex(conn)
    assert not bbt.exists


def test_native_takes_precedence_over_legacy():
    """When native keys exist, the legacy file is ignored."""
    conn = _native_conn([(1, 'ABC', 'native2020')])
    legacy = _legacy_file_blob([(1, 'ABC', 'legacy2020')])
    try:
        bbt = BetterBibTex(conn, legacy_dbpath=legacy)
        assert bbt.exists
        assert bbt.citekey('1_ABC') == 'native2020'
    finally:
        os.remove(legacy)


# --------------------------------------------------------------------
# Legacy standalone better-bibtex.sqlite (older Zotero / Better BibTeX)
# --------------------------------------------------------------------

def test_legacy_blob_format():
    """Old Zotero schema falls back to the JSON-blob legacy database."""
    conn = _native_conn([], with_field=False)
    legacy = _legacy_file_blob([(1, 'ABC', 'foo2020'), (2, 'XYZ', 'baz2021')])
    try:
        bbt = BetterBibTex(conn, legacy_dbpath=legacy)
        assert bbt.exists
        assert bbt.citekey('1_ABC') == 'foo2020'
        assert bbt.citekey('2_XYZ') == 'baz2021'
    finally:
        os.remove(legacy)


def test_legacy_table_format():
    """Old Zotero schema falls back to the `citationkey`-table legacy DB."""
    conn = _native_conn([], with_field=False)
    legacy = _legacy_file_table([(1, 'ABC', 'foo2020')])
    try:
        bbt = BetterBibTex(conn, legacy_dbpath=legacy)
        assert bbt.exists
        assert bbt.citekey('1_ABC') == 'foo2020'
    finally:
        os.remove(legacy)


def test_legacy_used_when_native_field_present_but_empty():
    """Native field with no keys still falls back to a legacy file."""
    conn = _native_conn([])  # field present, zero keys
    legacy = _legacy_file_table([(1, 'ABC', 'foo2020')])
    try:
        bbt = BetterBibTex(conn, legacy_dbpath=legacy)
        assert bbt.exists
        assert bbt.citekey('1_ABC') == 'foo2020'
    finally:
        os.remove(legacy)


# --------------------------------------------------------------------
# Nothing available
# --------------------------------------------------------------------

def test_no_bbt_modern_zotero():
    """Modern Zotero, no keys, no legacy file -> not available."""
    conn = _native_conn([])
    bbt = BetterBibTex(conn, legacy_dbpath=None)
    assert not bbt.exists


def test_no_bbt_old_zotero():
    """Old Zotero schema, no legacy file -> not available."""
    conn = _native_conn([], with_field=False)
    bbt = BetterBibTex(conn, legacy_dbpath='/no/such/better-bibtex.sqlite')
    assert not bbt.exists


# --------------------------------------------------------------------
# Standalone runner (so the suite works without pytest installed)
# --------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    funcs = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print('ok   ', fn.__name__)
        except Exception as err:  # noqa: B902
            failed += 1
            print('FAIL ', fn.__name__, '->', err)
    print('\n%d passed, %d failed' % (len(funcs) - failed, failed))
    sys.exit(1 if failed else 0)
