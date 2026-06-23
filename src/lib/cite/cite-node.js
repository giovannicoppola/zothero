#!/usr/bin/env node
// Node port of ZotHero's `cite` JXA script — same citeproc bundle,
// same CLI, byte-identical output. The JXA original costs ~3s/run,
// almost all of it Apple-JS runtime overhead loading the bundle; under
// Node the same work runs in well under a second.

'use strict'

const fs = require('fs')
const path = require('path')

// Load the citeproc UMD bundle extracted from src/lib/cite/cite.
// Under Node the UMD branch assigns to module.exports.
const CSL = require('./citeproc-bundle.js')

const usage = `cite [options] <style.csl> <csl.json>

Generate an HTML CSL citation for item defined in <csl.json> using
the stylesheet specified by <style.csl>.

Usage:
    cite [-b] [-v] [-l <lang>] [-L <dir>] <style.csl> <csl.json>
    cite (-h|--help)

Options:
        -b, --bibliography               Generate bibliography-style citation
        -l <lang>, --locale <lang>       Locale for citation
        -L <dir>, --locale-dir <dir>     Directory locale files are in
        -v, --verbose                    Show status messages
        -h, --help                       Show this message and exit

`

function showHelp(errMsg) {
    let status = 0
    if (errMsg) {
        console.error(`error: ${errMsg}`)
        status = 1
    }
    console.error(usage)
    process.exit(status)
}

function parseArgs(argv) {
    argv.forEach(s => {
        if (s == '-h' || s == '--help')
            showHelp()
    })
    if (argv.length == 0)
        showHelp()

    const args = []
    const opts = {
        locale: null,
        localeDir: './locales',
        style: null,
        csl: null,
        bibliography: false,
        verbose: false,
    }

    for (let i = 0; i < argv.length; i++) {
        const s = argv[i]
        if (s.startsWith('-')) {
            if (s == '--locale' || s == '-l') {
                opts.locale = argv[i + 1]
                i++
            } else if (s == '--locale-dir' || s == '-L') {
                opts.localeDir = argv[i + 1]
                i++
            } else if (s == '--bibliography' || s == '-b') {
                opts.bibliography = true
            } else if (s == '--verbose' || s == '-v') {
                opts.verbose = true
            } else {
                showHelp('unknown option: ' + s)
            }
        } else {
            args.push(s)
        }
    }

    if (args.length > 2)
        showHelp('script takes 2 arguments')
    if (args.length > 0)
        opts.style = args[0]
    if (args.length > 1)
        opts.csl = args[1]

    return opts
}

function readFile(p) {
    return fs.readFileSync(p, 'utf8')
}

function stripOuterDiv(html) {
    const match = new RegExp('^<div.*?>(.+)</div>$').exec(html)
    if (match != null)
        return match[1]
    return html
}

function Citer(opts) {
    this.opts = opts
    this.item = JSON.parse(readFile(opts.csl))
    this.style = readFile(opts.style)
    this.id = this.item.id

    let locale = 'en',
        force = false

    if (opts.locale) {
        locale = opts.locale
        force = true
    }

    this.citer = new CSL.Engine(this, this.style, locale, force)
}

Citer.prototype.retrieveItem = function (id) {
    return this.item
}

Citer.prototype.retrieveLocale = function (lang) {
    if (this.opts.verbose) {
        console.error(`locale=${lang}`)
        console.error(`localeDir=${this.opts.localeDir}`)
    }
    return readFile(path.join(this.opts.localeDir, `locales-${lang}.xml`))
}

Citer.prototype.cite = function () {
    const data = { html: '', rtf: '' }
    this.citer.updateItems([this.id])

    if (this.opts.bibliography) {
        const html = this.citer.makeBibliography()[1].join('\n').trim()
        data.html = stripOuterDiv(html)

        this.citer.setOutputFormat('rtf')
        data.rtf = this.citer.makeBibliography()[1].join('\n')
    } else {
        data.html = this.citer.makeCitationCluster([this.id])
        this.citer.setOutputFormat('rtf')
        data.rtf = this.citer.makeCitationCluster([this.id])
    }

    return data
}

const opts = parseArgs(process.argv.slice(2))

if (opts.verbose) {
    console.error(`bibliography=${opts.bibliography}`)
    console.error(`csl=${opts.csl}`)
    console.error(`style=${opts.style}`)
}

console.log(JSON.stringify(new Citer(opts).cite()))
