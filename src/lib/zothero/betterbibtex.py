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


SQL = "SELECT data FROM `better-bibtex` WHERE name = 'better-bibtex.citekey';"


class BetterBibTex(object):
    """Read citkeys from BetterBibTex database.

    Attributes:
        refkeys (dict): ``(library ID, item Key): citekey`` mapping.

    """

    def __init__(self, datadir):
        """Load Better Bibtex database from Zotero data directory.

        Args:
            datadir (unicode, optional): Zotero's data directory.

        Raises:
            RuntimeError: Raised if Better Bibtex database doesn't exist.

        """

        self._refkeys = {}
        self.exists = False
        dbpath = datadir

        if not os.path.exists(dbpath):
            return

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("ATTACH DATABASE ? AS betterbibtex", (dbpath,))

        # For newer version of Better Bibtex, a new table named `citationkey` is used.
        row = conn.execute(
            r"SELECT COUNT(*) FROM betterbibtex.sqlite_master WHERE type='table' AND name = 'citationkey'"
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
                    r"SELECT data FROM `better-bibtex` WHERE name = 'better-bibtex.citekey';"
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
