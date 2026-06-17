#!/usr/bin/env node
/**
 * voice-lint — the UX-QA guardrail (see docs/UX-QA.md).
 *
 * Fails the build when product copy contains AI-speak or wordy clichés that are
 * never appropriate. It does NOT police warmth: greetings, "You're in!", a
 * courteous "please", or an exclamation at a real milestone are human judgment
 * per the guide, not the linter's job. It scans only user-facing text (quoted
 * string literals + JSX text nodes) under src/, skipping tests.
 *
 * Run: npm run voice-lint   (wired into pr-checks.yml frontend job)
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const SRC = join(ROOT, 'src')

// Phrases that are never right in product copy. Lowercased; matched as
// substrings inside user-facing text. Kept tight to avoid false positives —
// borderline-but-sometimes-valid words (robust, leverage, journey) are
// deliberately NOT here; the guide covers them, the linter stays high-signal.
const BANNED = [
  // ── AI-speak / manufactured marketing ──
  ['dive in', 'plain verb — "start", "open"'],
  ["let's dive", 'plain verb — "let\'s start"'],
  ['delve', 'use "look at" / "go into"'],
  ['seamless', 'cut it — say what actually happens'],
  ['supercharge', 'cut it'],
  ["i'd be happy to", 'just do the thing'],
  ['great question', 'drop the filler — answer'],
  ['at the end of the day', 'cut it'],
  ['needless to say', 'cut it'],
  ['game-changer', 'cut it'],
  ['game changer', 'cut it'],
  ['cutting-edge', 'cut it'],
  ['cutting edge', 'cut it'],
  ['best-in-class', 'cut it'],
  ['unleash', 'cut it'],
  ['revolutioniz', 'cut it'],
  ['elevate your', 'say what concretely improves'],
  ['unlock your potential', 'say the concrete benefit'],
  ['empower', 'say what the user can actually do'],
  ['take your work anywhere', 'say the concrete action (export / download)'],
  // ── wordy clichés (always reducible) ──
  ['in order to', 'use "to"'],
  ['due to the fact that', 'use "because"'],
  ['at this point in time', 'use "now"'],
  ['in the event that', 'use "if"'],
  ['for the purpose of', 'use "to" / "for"'],
  ['with regard to', 'use "about"'],
  ['with regards to', 'use "about"'],
]

// Pictographic emoji only — decorative arrows (→, ›) used in code are NOT flagged.
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    const s = statSync(p)
    if (s.isDirectory()) walk(p, out)
    else if (/\.(ts|tsx)$/.test(name) && !/\.test\./.test(name) && !p.includes(`${join('src', 'test')}`))
      out.push(p)
  }
  return out
}

// User-facing candidate text: quoted string contents + JSX text nodes. Naive but
// effective — banned phrases don't appear in classNames, import paths, or keys,
// so those slip through harmlessly.
function candidates(src) {
  const out = []
  const strRe = /(['"`])((?:\\.|(?!\1).)*)\1/g
  let m
  while ((m = strRe.exec(src))) {
    if (/[a-z]{3,}/i.test(m[2])) out.push([m.index, m[2]])
  }
  const jsxRe = />([^<>{}]*[A-Za-z]{3,}[^<>{}]*)</g
  while ((m = jsxRe.exec(src))) out.push([m.index, m[1]])
  return out
}

const lineOf = (src, idx) => src.slice(0, idx).split('\n').length

let errors = 0
let warnings = 0
for (const file of walk(SRC)) {
  const src = readFileSync(file, 'utf8')
  const rel = relative(ROOT, file)
  for (const [idx, raw] of candidates(src)) {
    const text = raw.toLowerCase()
    for (const [phrase, fix] of BANNED) {
      if (text.includes(phrase)) {
        console.error(`✖ ${rel}:${lineOf(src, idx)}  "${phrase}" — ${fix}`)
        errors++
      }
    }
    if (EMOJI.test(raw)) {
      console.warn(`⚠ ${rel}:${lineOf(src, idx)}  emoji in copy — let the words carry it (warning)`)
      warnings++
    }
  }
}

console.error(`\nvoice-lint: ${errors} error(s), ${warnings} warning(s). Guide: docs/UX-QA.md`)
process.exit(errors > 0 ? 1 : 0)
