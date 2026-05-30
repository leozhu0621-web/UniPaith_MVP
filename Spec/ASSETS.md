# ASSETS · Embedded Brand & Source Asset Catalog

> Every asset a builder needs, with text-based assets (SVG, CSS) embedded verbatim and binary assets cataloged with path + usage + recommended destination. Goal: the spec set is self-contained — you should rarely need to open the original files.
>
> Status: **draft v1.0** · 2026-05-29 · Companion to `01-brand-tokens.md` (tokens) and `05-architecture.md` (diagrams).

---

## 1. Logo / wordmark SVGs (embedded verbatim)

All four wordmark variants share the same spec: Europa Regular 400, 56px default, −1.2 letter-spacing. Only color + surface change. Source: `Brand Materials/wordmark-*.svg`.

### wordmark-light.svg — transparent, for light surfaces
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 80" width="260" height="80">
  <title>UniPaith wordmark — light theme · transparent</title>
  <text x="17" y="58" font-family="Europa, system-ui, sans-serif" font-weight="400" font-size="56" letter-spacing="-1.2">
    <tspan fill="#FFD60A">U</tspan><tspan fill="#2A6BD4">ni</tspan><tspan fill="#FFD60A">P</tspan><tspan fill="#2A6BD4">aith</tspan>
  </text>
</svg>
```

### wordmark-dark.svg — transparent, for dark surfaces (lowercase → cream)
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 80" width="260" height="80">
  <title>UniPaith wordmark — dark theme · transparent</title>
  <text x="17" y="58" font-family="Europa, system-ui, sans-serif" font-weight="400" font-size="56" letter-spacing="-1.2">
    <tspan fill="#FFD60A">U</tspan><tspan fill="#F5F1E8">ni</tspan><tspan fill="#FFD60A">P</tspan><tspan fill="#F5F1E8">aith</tspan>
  </text>
</svg>
```

### wordmark-light-bg.svg — cream tile (self-contained)
Same `<text>` as wordmark-light, on a `<rect width="260" height="80" rx="8" fill="#FCFAF2"/>` behind it. Use for slide cards, social tiles, OG images, letterhead. Source file: `Brand Materials/wordmark-light-bg.svg`.

### wordmark-dark-bg.svg — navy tile (self-contained)
Same `<text>` as wordmark-dark, on a `<rect width="260" height="80" rx="8" fill="#0A1428"/>`. The version where yellow hits full strength. Use for app icon, social profile header, video splash. Source file: `Brand Materials/wordmark-dark-bg.svg`.

---

## 2. Favicon / UP monogram SVGs (embedded verbatim)

Source: `Brand Materials/favicon*.svg`. 64×64, 14px corner radius.

### favicon.svg — primary (blue UP on gold)
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <title>UniPaith favicon — blue UP on yellow</title>
  <rect x="0" y="0" width="64" height="64" rx="14" fill="#FFD60A"/>
  <text x="32" y="46" text-anchor="middle" font-family="Europa, 'Helvetica Neue', Inter, system-ui, sans-serif" font-weight="700" font-size="34" fill="#2A6BD4" letter-spacing="-1.6">UP</text>
</svg>
```

### favicon-dark.svg — dark (yellow UP on navy)
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <title>UniPaith favicon — dark · yellow UP on navy</title>
  <rect x="0" y="0" width="64" height="64" rx="14" fill="#0A1428"/>
  <text x="32" y="46" text-anchor="middle" font-family="Europa, 'Helvetica Neue', Inter, system-ui, sans-serif" font-weight="700" font-size="34" fill="#FFD60A" letter-spacing="-1.6">UP</text>
</svg>
```

> **First-paint caveat**: these embed Europa by name; before the Typekit kit loads, the glyphs fall back. For the browser tab `<link rel="icon">`, convert text→paths at export OR use rasterized PNGs (see §4).

---

## 3. Canonical CSS

`colors_and_type.css` is embedded verbatim in `01-brand-tokens.md` §11. It is the single source of truth for color, type, spacing, radii, elevation, and motion. Original location: `White-Paper/design_extracted/white-paper-template/project/assets/colors_and_type.css`.

---

## 4. Binary assets — catalog (path + usage + destination)

These cannot be embedded; cataloged for the builder.

### Wordmark rasters (`Brand Materials/`)
| File | Size | Use | → Destination |
|---|---|---|---|
| `wordmark-light-300.png` | 300px wide | Small light-surface raster | `frontend/public/og/` |
| `wordmark-light-2400.png` | 2400px | Hi-res light raster | OG / social |
| `wordmark-light-3000.png` | 3000px | Max light raster | print |
| `wordmark-dark-300/2400/3000.png` | — | Dark variants | same |
| `wordmark-light-bg-2400.png` | 2400px | Cream tile raster | social tiles |
| `wordmark-dark-bg-2400.png` | 2400px | Navy tile raster | app splash |

### Monogram export set (to GENERATE from favicon.svg)
Per brand guide, export at **16 / 32 / 48 / 64 / 180 / 192 / 512 px**. → `frontend/public/icons/up-{size}.png`. Corner radius scales with tile; mark never touches edge.

### Namecard (`Brand Materials/namecard-template.pptx`, `Misc./Leo-namecard.pdf`, `Misc./leo-namecard-{front,back}-staples.pdf`)
Business-card template + print-ready PDFs (Staples spec). Not app-relevant; reference for print brand consistency.

### Architecture diagrams (`Misc./`)
| File | Use |
|---|---|
| `UniPaith-Architecture-Flow.png` | Authoritative module-by-module flow (9 stages × student/shared/institution). Transcribed in `05-architecture.md` §1. |
| `UniPaith-Architecture-Flow_1/_2/_3.png` | Zoom variants of the same flow. |

### Prompt Map (`Misc./Prompt Map.pdf`)
2-page xmind. Page 1 "Incoming Info" (input tree), Page 2 "Outgoing Info" (output tree). Transcribed in `05-architecture.md` §3. Source for `40-prompt-library-schema.md`.

### QR code (`SV_bm8302fmH5xoV9A-qrcode.png`)
Survey QR (links to the OutReach Survey — Qualtrics `SV_bm8302fmH5xoV9A`). Marketing/research, not app.

---

## 5. Source documents — provenance map

Which source doc is authoritative for which spec:

| Source | Authoritative for | Spec consumer |
|---|---|---|
| `Master Paper.docx` | Vision, business model, feature definitions, Appendix A (typed Prompt Library I/O) | all feature specs |
| `Business Methodology.docx` | Operational schema precision, AI guardrails, intake thresholds, governance | `40`, `41`, `42`, `43` |
| `Misc./Prompt Library.docx` | **Deepest INPUT enumeration** — behavioral prompts, story bank, decision-psych, working-style, per-major tracks (untyped) | `40` §3 |
| Master Paper Appendix A | **Typed I/O** — Categorical/Numeric/Text tags + the OUTPUT half | `40` §3–§4 |
| `Misc./Feature List V1.docx` | Full feature checklist incl. net-new scope | `92-feature-backlog.md` |
| `Misc./Roadmap.docx` | Founder's intended phasing | `91-build-sequencing.md` |
| `Competition Analysis.docx` | 18 competitor profiles, moat taxonomy, threat verdicts | `06-product-context.md` |
| `OutReach Survey.docx` | Market-validated pain points, willingness-to-pay | `06-product-context.md` |
| `Platform_Presentation.pptx` | Investor narrative, "blockade" thesis | `06-product-context.md` |
| `UniPaith_Brand_Visual_Guide.pdf` | Human-readable brand guide | `01-brand-tokens.md` |
| `colors_and_type.css` | **Canonical brand tokens** | `01-brand-tokens.md` |
| `Brand Materials/*.svg` | Logo files | `01` §7, this doc |
| `Landing_MVP/` | Brand voice, taglines, fairness commitment, design language | `43`, `06` |
| `White-Paper/UniPaith-Whitepaper.html` | Typeset investor view (assembled) | reference only |

### Documents that are duplicate / archival (do not re-spec)
- `Master Paper (Restructured + Brand Guide).docx` — superseded by `Master Paper.docx`.
- `White-Paper/Master Paper.docx` + `White-Paper/Word DOCX/Whitepaper.docx` — typeset copies.
- `Old Plan.docx` — historical.
- `Misc./Business Plan.docx` ≡ `Misc./Platform_business_plan_Nonitalics.docx` — byte-identical.
- `Misc./Platform_Presentation.pptx` financials ≡ business plan.
- `.archive/` — pre-Claude landing-page code + screenshots; historical only.
- `Mail Merge - Email.docx` + `Mail Merge - Recipients.xlsx` + `OutReach List.xlsx` — outreach campaign ops, not product.

---

## 6. Fonts

- **Europa** via Adobe Fonts Typekit kit `spe3ioy` — `@import url('https://use.typekit.net/spe3ioy.css')`, family name lowercase `europa`. Ships 300/400/700 (+italics); no 600. Details in `01-brand-tokens.md` §3.
- The Landing_MVP marketing site uses a DIFFERENT stack (Lora + Inter + Caveat from Google Fonts) — that's the marketing-site brand, not the app. The app is Europa-only.

---

## 7. What to do first (asset setup checklist)

Per `91-build-sequencing.md` Phase 1:
- [ ] Add Typekit kit `spe3ioy` to `frontend/index.html`; verify domain allowlist.
- [ ] Copy `wordmark-light.svg` → `frontend/public/wordmark.svg`; `wordmark-dark.svg` → `frontend/public/wordmark-dark.svg`.
- [ ] Convert `favicon.svg` text→paths; export PNG set @ 16/32/48/64/180/192/512 → `frontend/public/icons/`.
- [ ] Place `favicon.svg` (paths) → `frontend/public/favicon.svg`.
- [ ] Generate OG image 1200×630 from `wordmark-light-bg` → `frontend/public/og/og-default.png`.
- [ ] Wire favicon + theme-color `<meta>` in `index.html` per `01` §7.3.
- [ ] Remove EB Garamond / Caveat / Kalam (G-B1).
