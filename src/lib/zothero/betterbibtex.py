# encoding: utf-8
#
# Copyright (c) 2020 @yarray
# Copyright (c) 2020 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

import json
import logging
import os
import sqlite3

from .util import timed

log = logging.getLogger(__name__)


# Modern Better BibTeX (>= 6.7, for Zotero 7) no longer keeps a separate
# `better-bibtex.sqlite` file. Instead it stores each item's citation key as a
# native `citationKey` field inside the Zotero database itself. These queries
# read it back out, mirroring Better BibTeX's own `KeyManager` load query.
NATIVE_FIELD_SQL = (
    "SELECT fieldID FROM fields WHERE fieldName = 'citationKey'"
)

NATIVE_LOAD_SQL = u"""
SELECT  item.libraryID AS libraryID,
        item.key AS itemKey,
        idv.value AS citationKey
    FROM items item
    JOIN itemData id ON item.itemID = id.itemID
    JOIN fields f ON id.fieldID = f.fieldID AND f.fieldName = 'citationKey'
    JOIN itemDataValues idv ON id.valueID = idv.valueID
"""


class BetterBibTex(object):
    """Read citekeys from Better BibTeX.

    Supports both modern Better BibTeX (citation keys stored as a native
    field in the Zotero database) and legacy versions (a standalone
    ``better-bibtex.sqlite`` file).

    Attributes:
        refkeys (dict): ``(library ID, item Key): citekey`` mapping.
        exists (bool): ``True`` if citation keys are available (i.e. Better
            BibTeX is installed, or the legacy database loaded). On modern
            Zotero ``citationKey`` is a native field, so "available" means at
            least one item actually has a citation key.

    """

    def __init__(self, conn=None, legacy_dbpath=None):
        """Load Better BibTeX citation keys.

        Args:
            conn (sqlite3.Connection, optional): Open connection to the
                Zotero database (the working copy). Used to read modern
                Better BibTeX citation keys from the native ``citationKey``
                field.
            legacy_dbpath (unicode, optional): Path to a legacy
                ``better-bibtex.sqlite`` database, used as a fallback for
                older Better BibTeX versions.

        """
        self._refkeys = {}
        self.exists = False

        # Modern Better BibTeX (>= 6.7, Zotero 7): citation keys live in the
        # Zotero database itself as a native `citationKey` field.
        if conn is not None and self._load_native(conn):
            self.exists = True
            return

        # Legacy Better BibTeX: a standalone better-bibtex.sqlite database.
        if legacy_dbpath and os.path.exists(legacy_dbpath):
            self._load_legacy(legacy_dbpath)

    def _load_native(self, conn):
        """Load citekeys from the Zotero database's ``citationKey`` field.

        Note: ``citationKey`` is a *native* Zotero field on modern versions
        (Zotero 7+), so its mere presence in the schema does NOT imply Better
        BibTeX is installed. We therefore treat the native source as
        "available" only when at least one item actually has a citation key.

        Args:
            conn (sqlite3.Connection): Open connection to the Zotero database.

        Returns:
            bool: ``True`` if at least one citation key was found.

        """
        row = conn.execute(NATIVE_FIELD_SQL).fetchone()
        if not row:  # field not in this (older) Zotero schema
            return False

        with timed("load Better Bibtex citekeys"):
            self._refkeys = {
                u'{}_{}'.format(r['libraryID'], r['itemKey']): r['citationKey']
                for r in conn.execute(NATIVE_LOAD_SQL)
            }
        return len(self._refkeys) > 0

    def _load_legacy(self, dbpath):
        """Load citekeys from a standalone ``better-bibtex.sqlite``.

        Args:
            dbpath (unicode): Path to the legacy Better BibTeX database.

        """
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("ATTACH DATABASE ? AS betterbibtex", (dbpath,))

        # For newer version of Better Bibtex, a new table named `citationkey`
        # is used.
        row = conn.execute(
            r"SELECT COUNT(*) FROM betterbibtex.sqlite_master "
            r"WHERE type='table' AND name = 'citationkey'"
        ).fetchone()
        is_newer_better_bibtex = row[0] == 1

        with timed("load Better Bibtex data"):
            if is_newer_better_bibtex:
                self._refkeys = {
                    str(ck["libraryID"]) + "_" + ck["itemKey"]: ck["citationKey"]
                    for ck in conn.execute(r"select * from betterbibtex.citationkey")
                }
            else:
                row = conn.execute(
                    r"SELECT data FROM `better-bibtex` "
                    r"WHERE name = 'better-bibtex.citekey';"
                ).fetchone()
                data = json.loads(row[0])["data"]
                self._refkeys = {
                    str(ck["libraryID"]) + "_" + ck["itemKey"]: ck["citekey"]
                    for ck in data
                }
        self.exists = True

    def citekey(self, key):
        """Return Better Bibtex citekey for Zotero item.

        Args:
            key (unicode): ``libraryID_itemKey`` Better Bibtex key.

        Returns:
            unicode: Citekey

        """

        return self._refkeys.get(key)
