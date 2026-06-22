# Plan: Fix slow citation copy/paste (issue #48)

Branch: `faster-citations` (off `master`). Tracking GitHub issue #48
("Copying of bibliographies and citation keys takes extremely long time").

Goal: bring citation copy from ~5–6s down to <1s, without breaking users who
don't have extra tooling installed, and without dropping existing features
(notably BetterBibTeX).

---

## Root causes (diagnosed + measured on this machine)

1. **citeproc-js runs under `osascript -l JavaScript` (JXA / JavaScriptCore).**
   This is the dominant cost. JavaScriptCore executes citeproc ~3.6× slower
   than node's V8. It is NOT osascript startup (an empty JXA call is 0.034s)
   and NOT bundle parsing (0.09s) — it's the engine *execution*.
   - Rebuilding the JXA bundle with newer citeproc (1.4.61) does **NOT** help
     (tested: chicago stayed ~5.8s). Only changing the *runtime* (node) helps.

2. **DB resync on the citation hot path.**  ✅ FIXED (commit 343f851).
   `do_copy → app.styles → zotero property` used to `copyifnewer()` the whole
   `zotero.sqlite` on every copy. Now the copy is lazy (only when the DB is
   actually queried for indexing/search). See "Done" below.

3. **Correctness bug on modern Chicago styles.**  TODO.
   Bundled citeproc predates CSL 1.0.2 and doesn't know
   `page-range-format="chicago-16"` → citing an entry *with a page range* in
   Chicago 17th/18th ed. crashes with `page_mangler is not a function`.
   This is masked by a **silent APA fallback** in `zh.py` do_copy that re-cites
   in APA/MLA/etc. and reports success — wrong output AND doubles the time.

### Benchmarks (per `cite` call, bibliography, test item)
| Style | JXA (current) | Node |
|---|---|---|
| ieee | 0.17s | 0.22s |
| apa | 2.85s | 0.79s |
| chicago-notes-bibliography | 5.67s | 1.36s |

`copyfile` of zotero.sqlite (cost removed from hot path by the sqlite fix):
1 MB ≈ 0.001s · 541 MB ≈ 0.24s · 1 GB ≈ 0.45s (faster SSD; slower disks worse —
fork dev reported ~1.5s on 541 MB).

---

## Done
- **sqlite lazy-copy fix** — commit `343f851` on `faster-citations`.
  - `zotero.py`: `Zotero.__init__` takes `live_dbpath`; `conn` does
    `copyifnewer(live → copy)` lazily on first connect; `last_updated` now uses
    the live DB's mtime.
  - `core.py`: `zotero` property no longer eager-copies; passes `live_dbpath`.
  - Verified: constructing Zotero / reading `styles_dir` / `last_updated` makes
    NO copy; opening `conn` makes the copy. Modules import clean.
  - Rationale preserved: the copy exists because Zotero locks the live DB
    (core.py:58). Indexing/search still copies; only the citation path skips it.

- **BetterBibTeX 9.x detection fix** — "Better BibTeX not installed" false alarm.
  - Root cause: modern BBT (>= 6.7, Zotero 7) dropped the standalone
    `better-bibtex.sqlite`. Citation keys are now a **native `citationKey`
    field inside `zotero.sqlite`** (`fields`/`itemData`/`itemDataValues`). The
    old `better-bibtex/` dir only holds `read-only.json` (pinned keys; `[]` here).
    ZotHero checked the dead file path → `bbt.exists=False` → false message.
    Verified on this machine: BBT 9.0.31, 9 keys present in `zotero.sqlite`.
  - `betterbibtex.py`: `BetterBibTex(conn, legacy_dbpath=...)` now reads the
    native `citationKey` field from the Zotero DB copy. NOTE: `citationKey` is a
    *native* Zotero 7 field (in core `fields`, fieldID 9, `customFields` empty),
    present even without BBT — so `exists` = "at least one citekey actually
    present", not just "field exists" (avoids a false positive on Zotero 7
    without BBT). Legacy standalone-file readers kept as a fallback for old BBT.
  - `zotero.py`: `bbt` property passes `self.conn` (+ optional legacy file). No
    more separate `better-bibtex.sqlite` copy.
  - `index.py`: `DB_VERSION` 8 → 9 (forces rebuild so citekeys repopulate);
    `bbt_available` flag written to `dbinfo` at index time and exposed as a
    property — lets the **search path read BBT-availability without copying the
    DB** (preserves the lazy-copy win above).
  - `zh.py`: `do_search`/`do_citekey` use `app.index.bbt_available` (index flag)
    + per-entry `e.citekey` instead of `zotero.bbt.exists` (which forced a copy).
    A keyless item under installed BBT now says "No citation key for this item".
  - Verified: native read (9 keys), no-BBT DB → `exists=False`, index flag
    round-trips, all files compile.

---

## TODO

### Phase A — Node citation backend with JXA fallback (the real fix)
1. Ship `src/lib/cite/cite-node.js` (node port of `cpjs/cite.js`).
   - Prototype already written and validated: `cpjs/cite-node.js` (byte-identical
     output vs JXA for apa + chicago). Move/adapt it into `src/lib/cite/`.
2. **Vendor citeproc for node** (users can't `npm install`): copy the single
   file `node_modules/citeproc/citeproc_commonjs.js` (~945 KB) into
   `src/lib/cite/` and `require()` it by relative path. (citeproc 1.4.61.)
3. Update `src/lib/cite/cite.py` `generate()`:
   - Detect node, prefer it, fall back to the existing JXA `cite` bundle if
     node is missing.
   - **Node detection must handle Alfred's minimal PATH** (omits Homebrew):
     check PATH + `/opt/homebrew/bin`, `/usr/local/bin`; allow an env override
     (e.g. `ZOTHERO_NODE`).
   - Same CLI/args as today (`-b`, `-l`, `-L`, `<style> <data>`); same
     `{html, rtf}` JSON contract.
4. Keep BetterBibTeX intact (do NOT follow the fork's removal of it).

### Phase B — Correctness fixes
1. The node path uses citeproc 1.4.61 → fixes `page_mangler` on modern Chicago.
   (JXA fallback keeps the old engine; document that it still fails on modern
   Chicago when node is absent.)
2. `zh.py` `do_copy` (~lines 370–414): remove/rework the **silent APA fallback**
   so citation errors surface as errors instead of returning wrong-style output.
   With node+1.4.61 the page_mangler crash shouldn't occur, so this becomes dead
   code to delete.

### Phase C — Validation
1. Output-parity harness: for ieee/apa/chicago, assert node output == JXA output
   (where JXA doesn't crash).
2. End-to-end copy timing before/after.
3. Test the node-missing fallback path explicitly.
4. Test on a real large library (current test DB is only 1.1 MB — too small to
   show the sqlite win or realistic timings).

### Phase D — Packaging / release
1. README: document the optional node requirement (without it → slow JXA
   fallback).
2. Bump version, build `.alfredworkflow`, publish as a GitHub Release asset
   (see release workflow established earlier).
3. Update issue #48.

---

## Open decisions (for Giovanni)
- **Node sourcing:** require system node (`brew install node`) + graceful JXA
  fallback [recommended], vs bundling a node binary (+30–50 MB, arch/notarization
  pain).
- **Coordinate with lutefiasco's PR** (fork: `lutefiasco/zotcott`) vs cherry-pick.
  The fork is a diverged separate product (renamed, new bundle ID, **BBT removed**,
  node mandatory, AI-authored) — treat as a *reference*, cherry-pick the engine +
  correctness fixes; don't merge wholesale.

## Key files
- `src/lib/cite/cite.py` — engine invocation (add node detect + fallback)
- `src/lib/cite/cite` — JXA bundle (fallback; unchanged)
- `src/lib/cite/cite-node.js` — NEW node runner (prototype: `cpjs/cite-node.js`)
- `src/lib/cite/citeproc_commonjs.js` — NEW vendored citeproc for node
- `src/zh.py` — `do_copy` (remove silent APA fallback)
- `src/lib/zothero/{zotero,core}.py` — sqlite fix (DONE)
- `cpjs/` — build tooling + source for the engines

## Working-tree note
`cpjs/cite-node.js` (prototype, untracked) and `cpjs/package.json` /
`package-lock.json` (citeproc bumped to ^2.4.63 during exploration) are NOT part
of the sqlite commit. `cpjs/node_modules/` is gitignored.

## Reference
- Fork: https://github.com/lutefiasco/zotcott (issue #48 commenter)
- Issue: https://github.com/giovannicoppola/zothero/issues/48
