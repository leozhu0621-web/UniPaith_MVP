# UniPaith Brand Guidelines

## Brand Voice

UniPaith speaks with two distinct voices depending on the audience.

### Student Voice — "Your Private Education Advisor"

**Tone:** Warm, encouraging, clear, personal. Like a knowledgeable friend guiding you through admissions.

- Use "you/your" language — speak directly to the student
- Be encouraging but honest — never vague or patronizing
- Keep language simple and jargon-free
- Celebrate progress, guide next steps

**Examples:**
- "Your profile is 72% complete — let's strengthen your activities section next."
- "Based on your goals, here are 5 programs worth exploring."
- "You're making great progress. Two more items and your application is ready to submit."

**Avoid:**
- Robotic language ("The system has determined...")
- Overly casual/slangy tone
- Anxiety-inducing urgency ("You MUST complete this NOW")

### Institution Voice — "AI Admission Operations System"

**Tone:** Professional, efficient, data-driven. Like a trusted consultant delivering operational intelligence.

- Lead with data and metrics
- Be concise and action-oriented
- Use precise, industry-standard terminology
- Frame insights in terms of operational impact

**Examples:**
- "12 applications are ready for review. 3 flagged items require attention."
- "Yield rate is up 8% this cycle. Top-performing campaign: Fall Open House."
- "Pipeline summary: 247 active, 18 decision-pending, 4 past deadline."

**Avoid:**
- Casual or chatty language
- Vague statements without data
- Marketing-speak aimed at students

### Shared Brand Voice

When speaking as UniPaith (landing pages, marketing, shared UI):
- Confident, transparent, modern
- "We simplify admissions" energy
- Neither too warm nor too cold — balanced and credible

---

## Color System

### Dual Theme System — Green+Gold (Students) / Blue+Gold (Institutions)

**Student theme**: `brand-green-*` (green) + `brand-amber-*` (gold)
**Institution theme**: `brand-slate-*` (blue) + `brand-amber-*` (gold)

#### Student Green Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-green-50` | `#F0FDF4` | Light student backgrounds |
| `brand-green-100` | `#DCFCE7` | Student fills, badges |
| `brand-green-200` | `#BBF7D0` | Student borders |
| `brand-green-300` | `#86EFAC` | Decorative green |
| `brand-green-400` | `#4ADE80` | Green hover states |
| `brand-green-500` | `#22C55E` | Secondary student green |
| `brand-green-600` | `#16A34A` | **Student primary** — buttons, links, accents |
| `brand-green-700` | `#15803D` | Student headings, dark sections |
| `brand-green-800` | `#166534` | Dark student text |
| `brand-green-900` | `#14532D` | Deepest student shade |

#### Institution Blue Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-slate-50` | `#F0F3F9` | Light institution backgrounds |
| `brand-slate-100` | `#E8EDF5` | Institution fills, badges |
| `brand-slate-200` | `#C9D3E8` | Institution borders |
| `brand-slate-300` | `#A3B3D4` | Decorative blue |
| `brand-slate-400` | `#7A91BC` | Muted institution icons |
| `brand-slate-500` | `#4E6A9E` | Secondary institution blue |
| `brand-slate-600` | `#3B5998` | **Institution primary** — buttons, links, accents |
| `brand-slate-700` | `#2C4370` | Institution headings, dark sections |
| `brand-slate-800` | `#1E2E4D` | Dark institution text |
| `brand-slate-900` | `#111B2E` | Deepest institution shade |

#### Shared Gold Accent

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-amber-50` | `#FFF8E7` | Warm accent backgrounds |
| `brand-amber-100` | `#FFEFC2` | Light amber fills |
| `brand-amber-200` | `#FFE08A` | Amber borders |
| `brand-amber-300` | `#FFCF4D` | Amber decorative |
| `brand-amber-400` | `#F5B800` | Amber hover |
| `brand-amber-500` | `#E5A100` | **Accent** — CTAs, highlights, energy |
| `brand-amber-600` | `#B8820D` | Amber on light backgrounds |
| `brand-amber-700` | `#8C6310` | Dark amber text |

### Audience Variations

**Student side** (green + gold):
- Background: `bg-student` (`#FAFAF8` — warm off-white)
- Primary: `brand-green-600` for buttons, links, active states
- Accent: `brand-amber-*` for CTAs, highlights, warmth
- Used on: homepage hero, /for-students, student sections, pricing student card

**Institution side** (blue + gold):
- Background: `bg-institution` (`#F8FAFC` — cool gray)
- Primary: `brand-slate-600` for buttons, links, active states
- Accent: `brand-amber-*` used sparingly for highlights
- Used on: /for-institutions, institution sections, pricing institution card

**Admin:**
- Dark sidebar (gray-900) with `brand-slate-600` active states

### Semantic Colors (shared, do not modify)

| Color | Hex | Usage |
|-------|-----|-------|
| Success | `#059669` (emerald-600) | Completed, accepted, verified |
| Warning | `#D97706` (amber-600) | Deadlines, attention needed |
| Danger | `#DC2626` (red-600) | Errors, rejected, destructive |
| Info | `#0284C7` (sky-600) | Informational, tips |

---

## Typography

**Font:** Inter (loaded via Google Fonts)

| Element | Weight | Size | Usage |
|---------|--------|------|-------|
| Page title | 700 (bold) | text-2xl | Main page headings |
| Section heading | 600 (semibold) | text-lg | Card/section titles |
| Body | 400 (regular) | text-sm | Default body text |
| Label | 500 (medium) | text-sm | Form labels, nav items |
| Caption | 400 (regular) | text-xs | Helper text, timestamps |
| Overline | 600 (semibold) | text-[11px] uppercase | Section labels in sidebars |

---

## Logo

Text-only mark: **Uni**Paith

- "Uni" in `brand-slate-600` (regular weight)
- "Paith" in `brand-slate-800` (extrabold weight)
- Rendered in Inter font family

```jsx
<span className="text-brand-slate-600">Uni</span>
<span className="text-brand-slate-800 font-extrabold">Paith</span>
```

---

## Component Conventions

### Buttons
- **Primary:** `bg-brand-slate-600 text-white hover:bg-brand-slate-700`
- **Secondary:** `border-brand-slate-200 text-brand-slate-700 hover:bg-brand-slate-50`
- **Ghost:** `text-brand-slate-700 hover:bg-brand-slate-50`
- **Danger:** `bg-rose-600 text-white hover:bg-rose-700`

### Links
- Default: `text-brand-slate-600 hover:underline`
- Navigation active: `text-brand-slate-700 font-medium` with `bg-brand-slate-50`

### Cards
- `bg-white rounded-2xl shadow-sm`
- Interactive: `hover:shadow-md transition-shadow`

### Form Inputs
- Focus ring: `focus:ring-brand-slate-600`
- Error border: `border-red-500`

### Tabs
- Active: `border-brand-slate-600 text-brand-slate-600`
- Inactive: `text-gray-500 hover:text-gray-700`

### Badges
- Keep semantic colors (success/warning/danger/info/neutral)
- Do not use brand colors for badges

---

## Usage Rules

1. **Brand-slate-600 is the primary action color** — use for buttons, links, active nav states
2. **Amber is the accent** — use sparingly for energy, highlights, and student-side warmth
3. **Never mix indigo/blue with brand-slate** — they are too similar and create visual confusion
4. **Keep semantic colors pure** — success is always emerald, danger is always rose/red
5. **Gray for neutrals** — text, borders, backgrounds that aren't brand-colored use Tailwind gray scale
6. **Student pages use slightly warmer neutrals** — achieved through the `bg-student` background
7. **Institution pages use cooler neutrals** — achieved through the `bg-institution` background
