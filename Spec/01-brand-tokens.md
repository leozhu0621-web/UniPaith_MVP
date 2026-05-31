# 01 · Brand Tokens — Source of Truth

> Canonical brand tokens for the UniPaith app. Every other spec references this file. Do not hardcode hex codes anywhere else; use the CSS variable / Tailwind alias names defined here.
>
> Status: **draft v1.1** · 2026-05-29 · Sources, in priority order:
> 1. **`colors_and_type.css`** — the single source of truth (found at `White-Paper/design_extracted/white-paper-template/project/assets/colors_and_type.css`; the file the brand HTML references). Full contents embedded in §11.
> 2. `UniPaith_Brand_Visual_Guide.pdf` (23pp) — the human-readable brand guide.
> 3. `Brand Materials/color-{palette,light-theme,dark-theme}.html` — earlier color exploration (superseded by #1 where they differ).
> 4. `Brand Materials/*.svg` + `wordmark-index.html` — the actual logo files (embedded in §7).
>
> **v1.1 corrections** (from reading the canonical CSS + SVG files): Europa loads via **Adobe Fonts Typekit**, not self-hosted woff2; there is **no Semibold 600 cut** (aliased to 700); status colors + radii reconciled to `colors_and_type.css`; wordmark/favicon SVG markup embedded; full semantic token set added.

---

## 1. Brand voice — visual

> "An editorial duotone — sunlit gold and cobalt blue against warm paper or deep ink. Status colors stay restrained so the brand pair holds attention." — `color-palette.html`

Operating principles (apply on every surface):

1. **Paper is the canvas.** Warm cream `#FCFAF2` dominates light surfaces. Pure white only for documents and print.
2. **Yellow is punctuation, not fill.** Sunlit gold appears on CTAs, brand caps in the wordmark, and accent moments. The rarest mark on a page — must feel earned.
3. **Cobalt is the workhorse accent.** Links, eyebrows, primary buttons (where gold would compete), interactive states.
4. **Soft Ink, not pure black, for body text.** Type sits softly on cream.
5. **Hierarchy from type weight + size + tracking — never from a second typeface.** Europa carries everything.
6. **Restraint over decoration.** No gradients, no drop shadows other than the three documented elevations, no decorative imagery on program detail pages.

---

## 2. Color tokens

All values match the canonical Brand Visual Guide. Where the PDF and the HTML refs differ, the **HTML wins** (more recent, includes status colors).

### 2.1 Primary palette

| Token | HEX | RGB | Role |
|---|---|---|---|
| `--primary` / `sunlit-gold` | `#FFD60A` | 255 214 10 | Capitals (U, P), accent moments, primary CTA, brand punctuation. |
| `--secondary` / `cobalt` | `#2A6BD4` | 42 107 212 | Lowercase wordmark, links, eyebrows, primary buttons. |
| `paper-cream` | `#FCFAF2` | 252 250 242 | Default light surface (`--bg` in light theme). |
| `deep-ink` | `#0A1428` | 10 20 40 | Default dark surface (`--bg` in dark theme). |

### 2.2 Neutrals

| Token | HEX | Role |
|---|---|---|
| `paper-cream` | `#FCFAF2` | Light bg. |
| `white` | `#FFFFFF` | Light surface (cards on cream), documents, print. |
| `warm-cream` | `#F5F1E8` | Dark-theme text, muted surface on light, lowercase wordmark on dark. |
| `muted-warm` | `#F2EEE0` | Muted light surface (sub-bands, callouts). |
| `soft-ink` | `#2A2724` | Body text on light. |
| `body-mut` | `#4A4640` | Muted body text on light. |
| `deep-ink` | `#0A1428` | Dark bg. |
| `dark-surface` | `#122039` | Dark-theme card / surface. |
| `dark-muted` | `#1A2C4D` | Dark-theme muted band. |
| `border-warm` | `#C9C2A8` | Hairlines & dividers on light. |
| `border-dark` | `#3F567C` | Hairlines & dividers on dark. |
| `text-mut-dark` | `#D9DEE8` | Muted body text on dark. |

### 2.3 Status colors

**Two source values exist — reconciled here.** The canonical `colors_and_type.css` is authoritative for the app; the color HTML refs were an earlier exploration. Use the **canonical** column.

| Role | Canonical (`colors_and_type.css`) | HTML-ref (superseded) | Light soft (bg) | Dark HEX (lifted) | Dark soft (bg) |
|---|---|---|---|---|---|
| success | `#2E7D5B` | `#1F6B2E` | `#DCE8DA` | `#6FCB95` | `#1E3A2A` |
| warning | `#C58A12` | `#B8741D` | `#F5E6CC` | `#F0B964` | `#3D2E18` |
| error / danger | `#B8412B` | `#B5321F` | `#F2D7D0` | `#FF8470` | `#3D1E1A` |
| info | `--secondary` (`#2A6BD4`) | — | — | `#6FA0E8` | — |

Status colors **must brighten on dark theme to hold contrast** (dark column). The soft-bg tints are not specified in `colors_and_type.css`; the values above come from the HTML refs and are retained as reasonable defaults — confirm with brand owner.

### 2.4 Dark theme brand adjustments

On Deep Ink, the brand pair shifts to hold contrast:

| Role | Light | Dark |
|---|---|---|
| `--primary` | `#FFD60A` | `#F2C800` (slightly desaturated gold) |
| `--secondary` | `#2A6BD4` | `#6FA0E8` (lifted cobalt) |
| `--text` | `#2A2724` soft ink | `#F5F1E8` warm cream |
| `--on-primary` | `#2A2724` ink | `#0A1428` deep ink |
| `--on-secondary` | `#FCFAF2` paper | `#0A1428` deep ink |

### 2.5 Full semantic token set (canonical)

The canonical CSS exposes a richer foreground/surface set than the simplified shadcn map. Use these for fine-grained text + border hierarchy:

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#FCFAF2` paper | `#0A1428` deep ink | Page background. |
| `--bg-muted` | `#F5F1E8` warm cream | `#0E1A30` | Muted section bands. |
| `--bg-raised` | `#FFFFFF` | `#122039` | Cards, raised surfaces. |
| `--bg-inverse` | `#0A1428` | `#FCFAF2` | Inverted callouts. |
| `--fg` | `#2A2724` soft ink | `#F5F1E8` warm cream | Body text. |
| `--fg-muted` | `#6B6660` | `#A7B0C0` | Secondary text, meta. |
| `--fg-subtle` | `#9A938A` | `#6E7889` | Placeholder, disabled, captions. |
| `--fg-on-accent` | `#2A2724` | `#0A1428` | Text on gold. |
| `--fg-on-dark` / `--fg-inverse` | `#F5F1E8` | `#2A2724` | Text on dark / inverted. |
| `--link` | `#2A6BD4` | `#6FA0E8` | Links. |
| `--link-hover` | `#1F58B5` | `#9CC0F0` | Link hover. |
| `--accent` | `#FFD60A` | `#F2C800` | Gold accent. |
| `--border-hair` | `#C9C2A8` | `#2A3552` | Default hairline. |
| `--border-soft` | `#E6DFCE` | `#1B2742` | Subtle separators. |
| `--border-strong` | `#948C7A` | `#4A5878` | Emphasized borders. |

### 2.6 Light + dark token map (shadcn bridge)

Frontend single source: `frontend/src/index.css` `@layer base` block. Tokens below are the contract; current index.css values are HSL-converted and match. (These are the shadcn-primitive variables; the canonical brand variables in §2.5 are the design source.)

```css
:root {                        /* LIGHT — default */
  --bg:               #FCFAF2;
  --surface:          #FFFFFF;
  --muted:            #F2EEE0;
  --text:             #2A2724;
  --text-mut:         #4A4640;
  --border:           #C9C2A8;
  --primary:          #FFD60A;
  --on-primary:       #2A2724;
  --secondary:        #2A6BD4;
  --on-secondary:     #FCFAF2;
  --accent:           #2A6BD4;   /* same as secondary; links/eyebrows */
  --success:          #1F6B2E;
  --success-soft:     #DCE8DA;
  --warning:          #B8741D;
  --warning-soft:     #F5E6CC;
  --error:            #B5321F;
  --error-soft:       #F2D7D0;
  --ring:             #FFD60A;
  --radius:           12px;
}

.dark, [data-theme="dark"] {   /* DARK */
  --bg:               #0A1428;
  --surface:          #122039;
  --muted:            #1A2C4D;
  --text:             #F5F1E8;
  --text-mut:         #D9DEE8;
  --border:           #3F567C;
  --primary:          #F2C800;
  --on-primary:       #0A1428;
  --secondary:        #6FA0E8;
  --on-secondary:     #0A1428;
  --accent:           #6FA0E8;
  --success:          #6FCB95;
  --success-soft:     #1E3A2A;
  --warning:          #F0B964;
  --warning-soft:     #3D2E18;
  --error:            #FF8470;
  --error-soft:       #3D1E1A;
  --ring:             #F2C800;
}
```

### 2.7 Proportion rule

**There are TWO documented proportions — these need to be reconciled before build.**

| Source | Paper | Ink | Cobalt | Gold |
|---|---|---|---|---|
| Brand Visual Guide PDF (p. 15) | 55% | 20% | 15% | 10% |
| `color-palette.html` (Usage Ratio bar) | 60% | 25% | 10% | 5% |

**Spec decision:** use **60·25·10·5** (the HTML — it's the more recent, more restrained ratio and matches the "yellow is punctuation, not fill" voice rule). Document the deviation when a screen meaningfully departs (e.g., the Discover Stage-1 hero may push gold to 8%).

---

## 3. Typography tokens

**Rule: one font — Europa.** Hierarchy comes from size, weight, and tracking — never a second typeface.

The current frontend `index.css` uses **EB Garamond** for headings and **Caveat / Kalam** for handwriting accents. **These must be removed.** See `47-current-vs-spec-gap-audit.md` G-B1 for the migration task.

### 3.1 How Europa is loaded — Adobe Fonts Typekit (NOT self-hosted)

Per the canonical `colors_and_type.css`:

```css
/* Europa is loaded from Adobe Fonts (Typekit kit spe3ioy). */
@import url('https://use.typekit.net/spe3ioy.css');
```

- Adobe Fonts exposes the family under the **lowercase name `europa`**.
- For the app, add the Typekit kit to `frontend/index.html` `<head>` (either the `@import` above in CSS, or the standard Typekit `<link rel="stylesheet" href="https://use.typekit.net/spe3ioy.css">`).
- The Typekit kit must whitelist the production domain `app.unipaith.co` and `localhost` for dev. Confirm the kit (`spe3ioy`) is owned by the UniPaith Adobe account and the domain allowlist includes the app domain.
- **No self-hosted `.woff2` needed** — this supersedes the earlier (incorrect) self-host plan.

```css
--font-sans: 'europa', sans-serif;        /* canonical token */
--font-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
```

Full Tailwind stack (with fallbacks for the brief window before the kit loads):
```css
font-family: 'europa', system-ui, -apple-system, 'Segoe UI', Roboto,
             'Helvetica Neue', Arial, sans-serif;
```

### 3.2 Weights in use — only THREE cuts in the kit

The Typekit kit `spe3ioy` ships **300 / 400 / 700 (+ italics)**. There is **no Semibold 600 cut.**

Per the canonical CSS:
```css
--fw-light:    300;
--fw-regular:  400;
--fw-semibold: 700;   /* ALIASED to Bold — the kit has no 600 */
--fw-bold:     700;
```

**Implication for the type scale:** anywhere this spec or the brand guide says "600 / Semibold" (H2, H3, eyebrow, UI label, button), the rendered weight is **700**. Do not author a `font-weight: 600` expecting a distinct cut — the browser would synthesize it. If a 600 cut is later added to the kit, update `--fw-semibold` here and it propagates.

Never italic for UI (italics exist in the kit but the brand voice avoids them). Never bolder than 700.

### 3.3 Type scale

Straight from `colors_and_type.css` (which matches the brand guide):

| Role | Weight token | Size | Tracking | Line-height | Notes |
|---|---|---|---|---|---|
| **Display** | bold (700) | 72px / 4.5rem | -0.02em | 1.05 | Hero only. Sparingly. |
| **Heading 1** | bold (700) | 48px / 3rem | -0.015em | 1.08 | Page title. |
| **Heading 2** | semibold (→700) | 28px / 1.75rem | 0 | 1.20 | Section title. |
| **Heading 3** | semibold (→700) | 20px / 1.25rem | 0 | 1.30 | Subsection. |
| **Body** | regular (400) | 16px / 1rem | 0 | 1.60 | Paragraph default. |
| **Body small** | regular (400) | 14px / 0.875rem | 0 | 1.50 | Meta, captions. |
| **Eyebrow** | semibold (→700) | 12px / 0.75rem | 0.22em | 1.20 | Uppercase, color = `--fg-muted` (canonical) or `--accent` (when it's a brand eyebrow). |
| **UI label** | semibold (→700) | 13px / 0.8125rem | 0 | 1.20 | Buttons, form labels. |

(H1 line-height is 1.08 per canonical CSS, vs 1.10 in the earlier draft — canonical wins.)

### 3.4 Weight role guide

- 300 (Light): hero subtitles, large quoted phrases.
- 400 (Regular): body, inputs, the wordmark.
- 700 (Semibold-aliased + Bold): H1–H3, Display, eyebrows, button labels, metric numbers.

### 3.4 Display rules

- Wordmark **"UniPaith"** is set in Europa Regular 400, tracking −1.2. U + P in `--primary`; lowercase in `--secondary` on light, `--text` (warm cream) on dark. Never re-spaced, never italicized, never any other weight.
- Below 80px wide on screen / 18mm wide in print, switch from the wordmark to the **UP monogram** (`favicon.svg` / `favicon-dark.svg`).

---

## 4. Spacing & layout

### 4.1 Spacing scale — 4px base

Matches Tailwind defaults: `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96`.

Every gap, padding, and margin must be a multiple of 4. The compiled CSS class for `p-3` is 12px, `p-6` is 24px, etc.

### 4.2 Container widths

| Tier | Max width | Use |
|---|---|---|
| `narrow` | 640px | Auth forms, single-column flows. |
| `default` | 1280px | Most authenticated pages. |
| `wide` | 1440px | Discovery results, dashboards. |
| `full` | 100% | Calendar, table-heavy admissions queues. |

Container padding: 16px mobile, 24px tablet, 32px desktop.

### 4.3 Border radius

**Two scales exist** — the canonical `colors_and_type.css` vs the app's current shadcn default. Use canonical for new work.

| Token | Canonical (`colors_and_type.css`) | App today (`index.css` shadcn) | Use |
|---|---|---|---|
| `--radius-xs` | 4px | — | Inline code, tiny chips. |
| `--radius-sm` | 6px | 8px (`--radius` − 4) | Inputs, small buttons, badges. |
| `--radius-md` | 10px | 10px (`--radius` − 2) | Default control. |
| `--radius` / `--radius-lg` | 14px (lg — "matches favicon tile") | 12px (default) | Cards, buttons, modals. |
| `--radius-xl` | 22px | — | Hero cards, large surfaces. |
| `--radius-pill` / `--radius-full` | 999px | 9999px | Chips, pill buttons. |

**Reconciliation note:** the app currently uses `--radius: 0.75rem` (12px) from shadcn. The canonical brand CSS uses lg=14px (matching the favicon tile corner). These are close; adopt the canonical 14px for cards to match the favicon, OR keep 12px app-wide for consistency — **confirm with brand owner** (see §10). Default this spec recommends: **14px for cards/tiles** (favicon match), 10px for inputs/controls, 6px for small chips.

### 4.4 Motion tokens

Per `colors_and_type.css`:

```css
--ease-out:    cubic-bezier(0.2, 0.7, 0.2, 1);
--ease-in-out: cubic-bezier(0.65, 0.05, 0.36, 1);
--dur-fast: 120ms;   /* hover, focus, small toggles */
--dur-base: 200ms;   /* most transitions */
--dur-slow: 360ms;   /* sheets, modals, stage transitions */
```

(The Landing_MVP marketing site uses a different curve — `cubic-bezier(0.22, 1, 0.36, 1)` at 200/300/700ms. The app uses the values above.)

---

## 5. Elevation

Three tiers — anything else is off-brand.

| Tier | Box-shadow (light) | Box-shadow (dark) | Use |
|---|---|---|---|
| `elev-subtle` | `0 1px 2px hsl(220 30% 10% / 0.06)` | `0 1px 2px hsl(0 0% 0% / 0.25)` | Default card resting state. |
| `elev-raised` | `0 8px 24px -8px hsl(220 30% 10% / 0.12)` | `0 8px 24px -8px hsl(0 0% 0% / 0.40)` | Hover, modal trigger, dropdown. |
| `elev-glow` | `0 0 0 2px var(--primary), 0 8px 24px -8px hsl(45 100% 50% / 0.25)` | same | Accent moments — selected state, success confirmation, the "this is the action" focal point. **Rare.** |

No other shadows. No gradients used as backgrounds. Drop shadow → ink-tinted only; never gray.

---

## 6. Iconography

- **Library:** `lucide-react` (already in the codebase).
- **Stroke width:** 1.5px default. 2px when an icon is the only label of a button.
- **Default color:** `currentColor`. Inherits from text color of parent. Never gold unless the icon IS the accent.
- **Sizes:** 16 · 20 · 24 · 32. Match the spacing scale.

---

## 7. Assets — embedded markup + paths

All brand assets live at `/Users/leozhu/Desktop/工作/UniPAith/Brand Materials/`. The SVGs are tiny and embedded below so a builder needs no external files. (A complete catalog of every asset incl. binaries lives in `ASSETS.md`.)

### 7.1 Wordmark — 4 variants, identical spec

Per `wordmark-index.html`. Same Europa Regular 400, 56px default, −1.2 letter-spacing across all four — only color + surface change.

| Variant | Caps | Lowercase | Surface | When |
|---|---|---|---|---|
| `wordmark-light.svg` | `#FFD60A` | `#2A6BD4` | transparent | Already on a light surface. |
| `wordmark-dark.svg` | `#FFD60A` | `#F5F1E8` (cream) | transparent | Already on a dark surface. |
| `wordmark-light-bg.svg` | `#FFD60A` | `#2A6BD4` | cream tile `#FCFAF2` | Need a self-contained light tile (slide cards, OG images). |
| `wordmark-dark-bg.svg` | `#FFD60A` | `#F5F1E8` | navy tile `#0A1428` | Need a self-contained dark tile (app icon, social header). |

**`wordmark-light.svg`** (embed verbatim):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 80" width="260" height="80">
  <title>UniPaith wordmark — light theme · transparent</title>
  <text x="17" y="58" font-family="Europa, system-ui, sans-serif" font-weight="400" font-size="56" letter-spacing="-1.2">
    <tspan fill="#FFD60A">U</tspan><tspan fill="#2A6BD4">ni</tspan><tspan fill="#FFD60A">P</tspan><tspan fill="#2A6BD4">aith</tspan>
  </text>
</svg>
```

**`wordmark-dark.svg`** (lowercase → cream):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 80" width="260" height="80">
  <title>UniPaith wordmark — dark theme · transparent</title>
  <text x="17" y="58" font-family="Europa, system-ui, sans-serif" font-weight="400" font-size="56" letter-spacing="-1.2">
    <tspan fill="#FFD60A">U</tspan><tspan fill="#F5F1E8">ni</tspan><tspan fill="#FFD60A">P</tspan><tspan fill="#F5F1E8">aith</tspan>
  </text>
</svg>
```

### 7.2 Favicon / UP monogram — 2 variants

**`favicon.svg`** (primary — blue UP on gold tile, 14px radius):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <title>UniPaith favicon — blue UP on yellow</title>
  <rect x="0" y="0" width="64" height="64" rx="14" fill="#FFD60A"/>
  <text x="32" y="46" text-anchor="middle" font-family="Europa, 'Helvetica Neue', Inter, system-ui, sans-serif" font-weight="700" font-size="34" fill="#2A6BD4" letter-spacing="-1.6">UP</text>
</svg>
```

**`favicon-dark.svg`** (yellow UP on navy tile):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <title>UniPaith favicon — dark · yellow UP on navy</title>
  <rect x="0" y="0" width="64" height="64" rx="14" fill="#0A1428"/>
  <text x="32" y="46" text-anchor="middle" font-family="Europa, 'Helvetica Neue', Inter, system-ui, sans-serif" font-weight="700" font-size="34" fill="#FFD60A" letter-spacing="-1.6">UP</text>
</svg>
```

> Note the monogram embeds Europa by family name. For favicons that must render before the Typekit kit loads (i.e., the browser tab icon), **convert text → vector paths** at export, OR rely on the rasterized PNGs. The live SVG-with-text favicon works once the font is available but is not guaranteed at first paint — prefer the PNG set for the actual `<link rel="icon">`.

### 7.3 Copy-to-public mapping

| Source | Destination | Use |
|---|---|---|
| `wordmark-light.svg` | `frontend/public/wordmark.svg` | Default app wordmark (navbar on light). |
| `wordmark-dark.svg` | `frontend/public/wordmark-dark.svg` | Dark theme wordmark. |
| `favicon.svg` | `frontend/public/favicon.svg` | Favicon (paths-converted). |
| `favicon-dark.svg` | `frontend/public/favicon-dark.svg` | Dark tile variant. |
| `wordmark-{light,dark}-{300,2400,3000}.png` | `frontend/public/og/` | OG / social raster sources. |
| (export) monogram PNGs @ 16/32/48/64/180/192/512 | `frontend/public/icons/` | Favicon + app icon + apple-touch. |

Favicon HTML in `frontend/index.html`:
```html
<link rel="icon" type="image/png" sizes="32x32" href="/icons/up-32.png" />
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="apple-touch-icon" sizes="180x180" href="/icons/up-180.png" />
<meta name="theme-color" content="#FCFAF2" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#0A1428" media="(prefers-color-scheme: dark)" />
```

Export the monogram at the seven sizes the brand guide specifies: **16 / 32 / 48 / 64 / 180 / 192 / 512 px**. Corner radius scales with tile; mark never touches the edge.

### 7.4 Wordmark hard rules (from the brand guide Misuse page)

- Never embolden — weight 400 only.
- Never italicize or slant.
- Never recolor — keep yellow caps (U, P) + cobalt/cream lowercase.
- Never re-space or change the cap rhythm.
- Below 80px wide on screen / 18mm in print → switch to the UP monogram.

---

## 8. Tailwind alias map

Recommended `tailwind.config.js` aliases so utility classes match token names. (Current config is ~80% there; gaps captured in `47-current-vs-spec-gap-audit.md`.)

```js
colors: {
  paper:        '#FCFAF2',
  cream:        '#F5F1E8',
  ink: {
    DEFAULT:    '#2A2724',     // soft ink (body text)
    deep:       '#0A1428',     // deep ink (dark canvas)
  },
  gold: {
    DEFAULT:    '#FFD60A',     // sunlit (light)
    dark:       '#F2C800',     // dark-theme
  },
  cobalt: {
    DEFAULT:    '#2A6BD4',
    dark:       '#6FA0E8',
  },
  border: {
    DEFAULT:    '#C9C2A8',     // warm beige
    dark:       '#3F567C',
  },
  muted: {
    DEFAULT:    '#F2EEE0',
    dark:       '#1A2C4D',
  },
  body: {
    DEFAULT:    '#4A4640',     // muted body
    dark:       '#D9DEE8',
  },
  success: { DEFAULT: '#1F6B2E', soft: '#DCE8DA', dark: '#6FCB95', 'dark-soft': '#1E3A2A' },
  warning: { DEFAULT: '#B8741D', soft: '#F5E6CC', dark: '#F0B964', 'dark-soft': '#3D2E18' },
  error:   { DEFAULT: '#B5321F', soft: '#F2D7D0', dark: '#FF8470', 'dark-soft': '#3D1E1A' },
},
fontFamily: {
  // Adobe Typekit exposes Europa as lowercase 'europa'. Kit: spe3ioy.
  sans: ['europa', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
  body: ['europa', 'system-ui', '-apple-system', 'sans-serif'],
  // NO heading/hwDisplay/hwNote — Europa carries everything.
},
fontWeight: {
  light: '300',
  normal: '400',
  semibold: '700',   // kit has no 600 cut — aliased to bold
  bold: '700',
},
fontSize: {
  display:  ['4.5rem',   { lineHeight: '1.05', letterSpacing: '-0.02em',  fontWeight: '700' }],
  h1:       ['3rem',     { lineHeight: '1.10', letterSpacing: '-0.015em', fontWeight: '700' }],
  h2:       ['1.75rem',  { lineHeight: '1.20', letterSpacing: '0',        fontWeight: '600' }],
  h3:       ['1.25rem',  { lineHeight: '1.30', letterSpacing: '0',        fontWeight: '600' }],
  body:     ['1rem',     { lineHeight: '1.60' }],
  small:    ['0.875rem', { lineHeight: '1.55' }],
  eyebrow:  ['0.75rem',  { lineHeight: '1.40', letterSpacing: '0.22em',   fontWeight: '600' }],
  label:    ['0.8125rem',{ lineHeight: '1.20',                            fontWeight: '600' }],
},
borderRadius: {
  sm:    '8px',
  DEFAULT:'12px',
  lg:    '16px',
  pill:  '9999px',
},
```

---

## 9. Compliance checklist (per surface)

Use this before merging a UI change.

- [ ] Every color references a token; no inline hex outside `index.css`.
- [ ] Type uses Europa stack only; no `font-heading`, no `Caveat`, no `Kalam`, no `EB Garamond`.
- [ ] Spacing is a multiple of 4.
- [ ] Shadow is one of the three documented elevations or none.
- [ ] On a light surface, gold + cobalt together cover ≤ 15% of the visual area.
- [ ] On a dark surface, the brand pair is swapped to the dark variants (`#F2C800`, `#6FA0E8`).
- [ ] No gradients, no decorative images, no color accents on **program detail pages** (`11-detail-pages-program.md` is editorial-only).
- [ ] Status color is the LIGHT or DARK variant matching the surface — never crossed.
- [ ] Wordmark is at ≥ 80px wide; otherwise the UP monogram is used.
- [ ] Eyebrow text is uppercase, 12px, 600 weight, tracking 0.22em, in `--accent`.
- [ ] Buttons honor the size/weight/radius rules in `02-design-system.md` §2.

---

## 10. Open questions / known gaps

- **Europa Typekit kit ownership + domain allowlist.** ~~Not on disk~~ — RESOLVED: Europa loads via Adobe Typekit kit `spe3ioy` (`@import url('https://use.typekit.net/spe3ioy.css')`). Remaining action: confirm the kit is on the UniPaith Adobe account and `app.unipaith.co` + `localhost` are in the kit's domain allowlist. If the kit is on a personal account, migrate it to the company account before launch.
- **No 600 cut.** The kit ships 300/400/700. `--fw-semibold` aliases to 700. If the brand wants a true Semibold, add the cut to the Typekit kit and update `--fw-semibold`.
- **Proportion rule reconciliation.** PDF says 55·20·15·10; HTML says 60·25·10·5. This spec uses 60·25·10·5. Confirm with the brand owner.
- **Radius reconciliation.** Canonical CSS lg=14px (favicon match); app shadcn default=12px. This spec recommends 14px cards / 10px controls / 6px chips. Confirm.
- **Status soft-bg tints.** `colors_and_type.css` defines only the solid status colors, not the soft backgrounds. The soft tints in §2.3 come from the HTML refs — confirm or regenerate from the canonical solids.
- **Color naming.** PDF uses both "Sunlit Yellow" and "Sunlit Gold"; HTML standardizes on "Sunlit Gold". This spec uses **Sunlit Gold**. (The canonical CSS comment says "Sunlit Yellow".) Pick one name for all customer-facing brand copy.
- **Favicon at first paint.** SVG-with-Europa-text favicon won't render the font before the kit loads. Convert favicon text→paths at export, or use the PNG set for `<link rel="icon">`. See §7.2.
- **OG image dimensions.** Recommend 1200×630, wordmark on `wordmark-light-bg.svg` cream tile, 80px clear space. Generate and place in `frontend/public/og/`.

---

## 11. Canonical CSS — `colors_and_type.css` (embedded verbatim)

This is the single source of truth. Reproduced in full so the spec is self-contained. Original at `White-Paper/design_extracted/white-paper-template/project/assets/colors_and_type.css`.

```css
/* =============================================================
   UniPaith — Colors & Type · single source of truth.
   Load on light surfaces by default; flip dark with
   [data-theme="dark"] on <html> or any container.
   ============================================================= */

/* FONTS — Europa from Adobe Fonts (Typekit kit spe3ioy). Europa-only. */
@import url('https://use.typekit.net/spe3ioy.css');

:root {
  /* TYPE STACK — Adobe exposes Europa as lowercase `europa`. */
  --font-sans: 'europa', sans-serif;
  --font-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;

  /* CORE PALETTE */
  --primary:        #FFD60A;   /* Sunlit Yellow — caps, punctuation, accent only */
  --primary-ink:    #2A2724;   /* foreground ON yellow */
  --secondary:      #2A6BD4;   /* Cobalt — lowercase, links, primary buttons */
  --secondary-ink:  #FCFAF2;   /* foreground ON cobalt */
  --paper-cream:    #FCFAF2;   /* default light surface */
  --warm-cream:     #F5F1E8;   /* muted surface · inverted lowercase on dark */
  --soft-ink:       #2A2724;   /* body text on light (not pure black) */
  --deep-ink:       #0A1428;   /* dark surface */
  --border:         #C9C2A8;   /* hairlines & dividers */
  --primary-dark:   #F2C800;   /* primary on Deep Ink — muted to hold contrast */
  --secondary-dark: #6FA0E8;   /* secondary on Deep Ink — lifted */
  --surface-dark:   #122039;   /* raised surface on dark theme */

  /* SEMANTIC SURFACES (light) */
  --bg: var(--paper-cream); --bg-muted: var(--warm-cream); --bg-raised: #FFFFFF; --bg-inverse: var(--deep-ink);
  --fg: var(--soft-ink); --fg-muted: #6B6660; --fg-subtle: #9A938A;
  --fg-on-accent: var(--primary-ink); --fg-on-dark: var(--warm-cream); --fg-inverse: var(--warm-cream);
  --link: var(--secondary); --link-hover: #1F58B5; --accent: var(--primary);
  --border-hair: var(--border); --border-soft: #E6DFCE; --border-strong: #948C7A;

  /* STATE */
  --success: #2E7D5B; --warning: #C58A12; --danger: #B8412B; --info: var(--secondary);

  /* SPACING — 4px base */
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px;
  --space-6:24px; --space-8:32px; --space-10:40px; --space-12:48px; --space-16:64px; --space-20:80px; --space-24:96px;

  /* RADII */
  --radius-xs:4px; --radius-sm:6px; --radius-md:10px; --radius-lg:14px; --radius-xl:22px; --radius-pill:999px;

  /* ELEVATION */
  --shadow-subtle: 0 1px 2px rgba(10,20,40,.06), 0 1px 1px rgba(10,20,40,.04);
  --shadow-raised: 0 6px 16px -4px rgba(10,20,40,.12), 0 2px 4px rgba(10,20,40,.06);
  --shadow-glow:   0 0 0 4px rgba(255,214,10,.18), 0 10px 30px -8px rgba(255,214,10,.45);

  /* MOTION */
  --ease-out: cubic-bezier(0.2,0.7,0.2,1); --ease-in-out: cubic-bezier(0.65,0.05,0.36,1);
  --dur-fast:120ms; --dur-base:200ms; --dur-slow:360ms;

  /* TYPE TOKENS — kit has 300/400/700 only; semibold aliased to 700 */
  --fw-light:300; --fw-regular:400; --fw-semibold:700; --fw-bold:700;
  --display-size:72px; --display-line:1.05; --display-track:-0.02em;
  --h1-size:48px; --h1-line:1.08; --h1-track:-0.015em;
  --h2-size:28px; --h2-line:1.20; --h2-track:0;
  --h3-size:20px; --h3-line:1.30; --h3-track:0;
  --body-size:16px; --body-line:1.60; --body-track:0;
  --small-size:14px; --small-line:1.50; --small-track:0;
  --eyebrow-size:12px; --eyebrow-line:1.20; --eyebrow-track:0.22em;
}

[data-theme="dark"] {
  --bg: var(--deep-ink); --bg-muted:#0E1A30; --bg-raised: var(--surface-dark); --bg-inverse: var(--paper-cream);
  --fg: var(--warm-cream); --fg-muted:#A7B0C0; --fg-subtle:#6E7889;
  --fg-on-accent: var(--deep-ink); --fg-on-dark: var(--warm-cream); --fg-inverse: var(--soft-ink);
  --primary: var(--primary-dark); --secondary: var(--secondary-dark);
  --link: var(--secondary-dark); --link-hover:#9CC0F0;
  --border-hair:#2A3552; --border-soft:#1B2742; --border-strong:#4A5878;
  --shadow-subtle: 0 1px 2px rgba(0,0,0,.5);
  --shadow-raised: 0 8px 20px -4px rgba(0,0,0,.55);
  --shadow-glow:   0 0 0 4px rgba(242,200,0,.22), 0 10px 30px -8px rgba(242,200,0,.40);
}
::selection { background: var(--primary); color: var(--primary-ink); }
```

The CSS also ships semantic type classes (`.u-display`, `.u-h1`–`.u-h3`, `.u-body`, `.u-small`, `.u-eyebrow`) bound to these tokens — reuse them or map to Tailwind `fontSize` per §8.
