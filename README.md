<div align="center">
    <img src="./src/icon.png" width="200" height="200">
</div>


ZotHero
=======

[Alfred][alfred] workflow for rapidly searching your Zotero database and copying citations.

Original by Dean Jackson ([@deanishe](https://github.com/deanishe))

<a href="https://github.com/giovannicoppola/zothero/releases/latest/">
<img alt="Downloads"
src="https://img.shields.io/github/downloads/giovannicoppola/zothero/total?color=purple&label=Downloads"><br/>
</a>
<a href="https://alfred.app/workflows/giovannicoppola/zothero/">
<img alt="Gallery Downloads"
src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fgiovannicoppola%2Falfred-gallery-downloads%2Fmain%2Fdownloads.json&query=%24.zothero%5B0%5D.display&label=Gallery%20Downloads&color=blue&logo=alfred"><br/>
</a>

<!-- MarkdownTOC autolink="true" bracket="round" depth="3" autoanchor="true" -->

- [Features](#features)
- [Download & installation](#download--installation)
- [Usage](#usage)
    - [Pasting citations](#pasting-citations)
- [Configuration](#configuration)
    - [Zotero data](#zotero-data)
    - [Citation styles](#citation-styles)
    - [Locales](#locales)
    - [All settings](#all-settings)
    - [Configuration sheet](#configuration-sheet)
- [Licence & thanks](#licence--thanks)
- [Changelog](#changelog)

<!-- /MarkdownTOC -->


<a name="features"></a>
Features
--------

- Perform full-text search across your Zotero database, including only searching specific fields
- NASA ADS-style first-author search (`zot ^name`) — match entries by first author's last name, sorted by author and year
- Open an entry's PDF directly in Zotero's built-in reader (optional, via `OPEN_PDF`)
- Copy citations using any [CSL][csl] style you have installed in Zotero
- Copy citations either in citation/note style or bibliography style
- Copy citations in any [locale supported by CSL](#locales)
- Copy Better BibTeX citekeys
- Citations are copied in multiple formats, so the right data are automatically pasted into the application you're using
- Trigger search while you type using the Snippet Trigger (you must assign the snippet keyword yourself in Alfred Preferences)


<a name="download--installation"></a>
Download & installation
-----------------------

Download the `ZotHero-XYZ.alfredworkflow` file from [GitHub releases](https://github.com/giovannicoppola/zothero/releases), and double-click the downloaded file to install.

**Note**: Versions 2.0 and later are only compatible with Alfred 5. If you're still using Alfred 4, download [v1.99.7][v1.99.7].

**Recommended:** Install [Node.js](https://nodejs.org) (e.g. `brew install node`). When present, ZotHero uses a much faster citation engine (~4× faster) that also supports modern Chicago page-range styles. Without Node, it falls back to a slower built-in engine, and some Chicago styles won't work. If your `node` is in a non-standard location, set `ZOTHERO_NODE` to its full path in the [configuration sheet][conf-sheet].


<a name="usage"></a>
Usage
-----

These are the workflow's default keywords in Alfred:

- `zot <query>` — Search your Zotero database (common fields).
    - `zot ^<name>` — NASA ADS-style first-author search: only matches entries whose first author's last name starts with `<name>`, sorted by author name and year (newest first).
    - `↩` — Open the entry in Zotero. (`fn+↩` is an alternate)
        - If `OPEN_PDF` is enabled in the configuration sheet, `↩` instead opens the entry's PDF in Zotero's built-in reader (entries without a PDF still select in Zotero). `fn+↩` then selects the item, and on entries you didn't open with `↩`, `fn+↩` offers "Open PDF in Zotero".
    - `⌘↩` — Copy citation to the pasteboard (see [Configuration](#configuration)).
    - `⌥↩` — Copy bibliography-style citation to the pasteboard (see [Configuration](#configuration)).
    - `⇧↩` — View entry attachments (if present).
        - `↩` — Open an attachment in the default application.
    - `^↩` — View all citation styles.
        - `↩` or `⌘↩` — Copy citation in selected style.
        - `⌥↩` — Copy bibliography-style citation in selected style.
        - `^↩` — Set style as default.
    - This search can also be triggered by typing a snippet (which you must first assign yourself in Alfred Preferences)
    - When the Better-Bibtex plugin for Zotero is installed and `COPY_CITEKEY_MOD` is set to any of `-`(no modifier), `alt`, `ctrl`, `cmd`, `fn`, `shift`, the "Copy citekey" functionality can be enabled to override above operations

- `zot:[<query>]` — Search a specific field.
    - `↩` — Select a field to search against.
- `zotconf [<query>]` — View and edit workflow configuration.
    - `Default Style: …` — Choose a citation style for the `⌘↩` and `⌥↩` hotkeys (on search results).
    - `Locale: …` — Choose a locale for the formatting of citations. If unset, the default for the style is used, or if none is set, US English.
    - `Reload Zotero Cache` — Clear the workflow's cache of Zotero data. Useful if the workflow gets out of sync with Zotero.
    - `Open Log File` — Open the workflows log file in the default app (usually Console.app). Useful for checking on indexing problems (the indexer output isn't visible in Alfred's debugger).
    - `View Documentation` — Open this README in your browser.
    - `Report an Issue` — Open the GitHub issue tracker in your browser.


<a name="pasting-citations"></a>
### Pasting citations ###

When you copy a citation, ZotHero puts both HTML and rich text (RTF) representations on the pasteboard. That way, when you paste a citation into an application like Word, the formatted text will be pasted, but when you paste into a text/Markdown document, the HTML will be pasted.


<a name="configuration"></a>
Configuration
-------------

The workflow reads Zotero's own config files and partly manages its own configuration with the keyword `zotconf`, but you may need to use the [workflow configuration sheet][conf-sheet] if the workflow can't read Zotero's config files.

**NOTE:** Unlike its main database, Zotero does not save changes to its configuration until the application closes. As such, if you change Zotero's data or attachment directories, the workflow won't see the changes until you quit Zotero.


<a name="zotero-data"></a>
### Zotero data ###

The workflow uses your Zotero database and styles, therefore it needs to know where to find them. The workflow tries to read Zotero's own configuration files, and falls back to `~/Zotero` (the default location for Zotero 5).

If the workflow can't find your data, you need to set `ZOTERO_DIR` in the [workflow configuration sheet][conf-sheet].

Similarly, if you have set a "Linked Attachment Base Directory" in Zotero, but the workflow can't find the directory, enter its path for `ATTACHMENTS_DIR` in the [configuration sheet][conf-sheet].

**Note**: You can use the UNIX shortcut `~` to represent your home directory, e.g. `~/Zotero` for Zotero 5's default directory.


<a name="citation-styles"></a>
### Citation styles ###

The workflow uses the CSL styles you have installed in Zotero, so to add a new style, simply add it in Zotero. The workflow will pick up the new style(s) on the next run.

You can copy either a citation-/note-style citation or a bibliography-style one by hitting `⌘↩` or `⌥↩` respectively on a search result or citation style.

For `⌘↩` and `⌥↩` to work on search results, you must first choose a default style. You can either do this in the configuration screen (keyword `zotconf`), or hitting `^↩` on a search result to show all citation styles, then `^↩` on a style to set that as the default.


<a name="locales"></a>
### Locales ###

[CSL][csl] and ZotHero support the following locales. The default behaviour is to use the locale specified in the style if there is one, and `en-US` (American English) if not. Setting a locale overrides the style's own locale.

Use the `zotconf` keyword to force a specific locale.

|                    Locale                    |   Code  |
|----------------------------------------------|---------|
| Afrikaans                                    | `af-ZA` |
| Bahasa Indonesia / Indonesian                | `id-ID` |
| Català / Catalan                             | `ca-AD` |
| Cymraeg / Welsh                              | `cy-GB` |
| Dansk / Danish                               | `da-DK` |
| Deutsch (Deutschland) / German (Germany)     | `de-DE` |
| Deutsch (Schweiz) / German (Switzerland)     | `de-CH` |
| Deutsch (Österreich) / German (Austria)      | `de-AT` |
| Eesti / Estonian                             | `et-EE` |
| English (UK)                                 | `en-GB` |
| English (US)                                 | `en-US` |
| Español (Chile) / Spanish (Chile)            | `es-CL` |
| Español (España) / Spanish (Spain)           | `es-ES` |
| Español (México) / Spanish (Mexico)          | `es-MX` |
| Euskara / Basque                             | `eu`    |
| Français (Canada) / French (Canada)          | `fr-CA` |
| Français (France) / French (France)          | `fr-FR` |
| Hrvatski / Croatian                          | `hr-HR` |
| Italiano / Italian                           | `it-IT` |
| Latviešu / Latvian                           | `lv-LV` |
| Lietuvių / Lithuanian                        | `lt-LT` |
| Magyar / Hungarian                           | `hu-HU` |
| Nederlands / Dutch                           | `nl-NL` |
| Norsk bokmål / Norwegian (Bokmål)            | `nb-NO` |
| Norsk nynorsk / Norwegian (Nynorsk)          | `nn-NO` |
| Polski / Polish                              | `pl-PL` |
| Português (Brasil) / Portuguese (Brazil)     | `pt-BR` |
| Português (Portugal) / Portuguese (Portugal) | `pt-PT` |
| Română / Romanian                            | `ro-RO` |
| Slovenčina / Slovak                          | `sk-SK` |
| Slovenščina / Slovenian                      | `sl-SI` |
| Suomi / Finnish                              | `fi-FI` |
| Svenska / Swedish                            | `sv-SE` |
| Tiếng Việt / Vietnamese                      | `vi-VN` |
| Türkçe / Turkish                             | `tr-TR` |
| Íslenska / Icelandic                         | `is-IS` |
| Čeština / Czech                              | `cs-CZ` |
| Ελληνικά / Greek                             | `el-GR` |
| Български / Bulgarian                        | `bg-BG` |
| Монгол / Mongolian                           | `mn-MN` |
| Русский / Russian                            | `ru-RU` |
| Српски / Srpski / Serbian                    | `sr-RS` |
| Українська / Ukrainian                       | `uk-UA` |
| עברית / Hebrew                               | `he-IL` |
| العربية / Arabic                             | `ar`    |
| فارسی / Persian                              | `fa-IR` |
| ไทย / Thai                                   | `th-TH` |
| ភាសាខ្មែរ / Khmer                            | `km-KH` |
| 中文 (中国大陆) / Chinese (PRC)              | `zh-CN` |
| 中文 (台灣) / Chinese (Taiwan)               | `zh-TW` |
| 日本語 / Japanese                            | `ja-JP` |
| 한국어 / Korean                              | `ko-KR` |


<a name="all-settings"></a>
### All settings ###

Theses are all settings available in the [workflow configuration sheet][conf-sheet].

You probably shouldn't edit the `CITE_STYLE` or `LOCALE` variables yourself, as there's no guarantee the value you set is actually available. Adjust them using the `zotconf` keyword.


|      Variable      |                                 Meaning                                 |
|--------------------|-------------------------------------------------------------------------|
| `ATTACHMENTS_DIR`  | Path to your Zotero attachments. Read from Zotero's config by default.  |
| `CITE_STYLE`       | Citation style copied by `⌘↩` and `⌥↩`                                  |
| `LOCALE`           | Locale for citations. Default: `en-US` (US English).                    |
| `ZOTERO_DIR`       | Path to your Zotero data. Read from Zotero's config by default.         |
| `COPY_CITEKEY_MOD` | Set to copy Better BibTeX citekey instead of CSL citation/bibliography. |
| `OPEN_PDF`         | When enabled, `↩` opens the entry's PDF in Zotero's reader instead of selecting the item. |
| `ZOTHERO_NODE`     | Optional path to a `node` executable for the fast citation engine. Auto-detected if unset. |



<a name="licence--thanks"></a>
Licence & thanks
----------------

This workflow is released under the [MIT licence][licence].

It is heavily based on [Alfred-Workflow][aw] (also MIT) for the workflow stuff, and [citeproc-js][citeproc-js] ([AGPL][citeproc-licence]) for generating the citations.

It was inspired by the now-defunct [ZotQuery][zotquery] by [@fractaledmind][smargh].

The [Zorro icon][icon-source] was created by [Dan Lowenstein][lowenstein] from [the Noun Project][noun-project].


<a name="changelog"></a>
Changelog
----------------

- 2026-06-23 Version 2.6: NASA ADS-style first-author search (`^name`), plus an
  optional setting to open an entry's PDF directly in Zotero's reader. Thanks to
  [@zhouconghao](https://github.com/zhouconghao) for the first-author search
  ([#51](https://github.com/giovannicoppola/zothero/pull/51)), and to
  [@ljci](https://github.com/ljci) ([#44](https://github.com/giovannicoppola/zothero/issues/44))
  and [@flin16](https://github.com/flin16) ([#47](https://github.com/giovannicoppola/zothero/issues/47))
  for proposing the open-in-Zotero feature.
- 2026-06-23 Version 2.5: optional Node citation backend (~4× faster citations)
  with citeproc 1.4.61 (fixes the Chicago page-range crash), and citation errors
  are now surfaced honestly instead of silently falling back to another style.
  Thanks to [@lutefiasco](https://github.com/lutefiasco) for the Node backend
  ([#52](https://github.com/giovannicoppola/zothero/pull/52),
  [#53](https://github.com/giovannicoppola/zothero/pull/53)),
  [@zhouconghao](https://github.com/zhouconghao) for reading native citekeys when
  `better-bibtex.sqlite` is missing ([#50](https://github.com/giovannicoppola/zothero/pull/50)),
  and to [@burgershot](https://github.com/burgershot) ([#48](https://github.com/giovannicoppola/zothero/issues/48))
  and [@SdotVdot](https://github.com/SdotVdot) ([#49](https://github.com/giovannicoppola/zothero/issues/49))
  for reporting the slow-citation and Zotero-9 issues.
- 2026-06-22 Version 2.4.1: restore copy-citekey under modern Better BibTeX /
  Zotero 7 (native `citationKey` field) and make the citation-copy SQLite copy lazy.
- 2025-10-07 Version 2.4: restored auto-paste when using the snippet trigger,
  fixed the Better BibTeX requirement, and fixed the "0 day" bug in date
  formatting. Thanks to [@johannrichard](https://github.com/johannrichard)
  ([#32](https://github.com/giovannicoppola/zothero/issues/32)) for reporting the date bug.
- 2025-09-30 Version 2.3.1: citation handling fixes.
- 2025-09-29 Version 2.3: improvements to citation and citekey handling.
- 2023-11-23 Version 2.2: added support for newer BetterBibtex (thanks [@fty1777](https://github.com/fty1777) and [@retorquere](https://github.com/retorquere))
- 2022-12-15 Version 2.1
- 2022-11-27 Version 2.0 updated for Alfred 5

[alfred]: https://www.alfredapp.com/
[aw]: http://www.deanishe.net/alfred-workflow/
[citeproc-licence]: https://github.com/Juris-M/citeproc-js/blob/master/AGPLv3
[citeproc-js]: https://github.com/Juris-M/citeproc-js
[conf-sheet]: https://www.alfredapp.com/help/workflows/advanced/variables/#environment
[csl]: http://citationstyles.org
[icon-source]: https://thenounproject.com/term/zorro/14540/
[licence]: ./LICENCE
[lowenstein]: https://thenounproject.com/danny_mustache
[noun-project]: https://thenounproject.com
[releases]: https://github.com/giovannicoppola/zothero/releases
[smargh]: https://github.com/fractaledmind
[zotquery]: https://github.com/fractaledmind/alfred_zotquery
[v1.99.7]: https://github.com/giovannicoppola/zothero/releases/tag/v1.99.7
