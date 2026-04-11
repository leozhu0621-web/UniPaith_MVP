# UniPaith Brand Guidelines

## Brand Identity

**Name:** UniPaith (Uni = universal, Paith = path)
**Tagline:** Your private college advisor
**Positioning:** Everything a $6K agent does — for free. Smart matching, application management, and guidance for students. AI admissions operations for institutions.

---

## Brand Voice

### Student Voice — Friendly Expert

Like a great college counselor who's also a good friend. Confident, concrete, direct.

- Lead with outcomes, not AI. Show what UniPaith does; mention AI as the how.
- Be specific: numbers, features, concrete examples.
- Friendly and comfortable — but never therapist-y.
- "You" language — speak directly to the student.

**Do:**
- "We found 8 programs that match your budget and goals."
- "Your readiness score is 74 — here's what to work on."
- "3 programs in Germany have zero tuition for international students."

**Don't:**
- "We understand how stressful this process can be..." (therapist)
- "AI-powered guidance from first thought to final decision" (vague poetry)
- "Free forever, no catches, no credit card" (sounds desperate)
- "The system has determined..." (robotic)

### Institution Voice — Professional Operator

Like a sharp consultant delivering operational results. Data-forward, concise.

- Lead with operational impact, not feature lists.
- Use precise, industry-standard terminology.
- Frame insights in terms of time saved, yield improved, pipeline clarity.

**Do:**
- "12 applications ready for review. 3 flagged for attention."
- "Yield rate up 8% this cycle."
- "AI-prioritized queue with rubric-aligned summaries."

**Don't:**
- Casual or chatty language.
- Marketing-speak aimed at students.
- Vague claims without numbers.

### Shared Voice (Homepage, About, Engine)

Confident and transparent. Neither too warm nor too cold.
"We simplify admissions" energy — balanced and credible.

---

## Color System

UniPaith uses a two-mode color system: **Forest Green** for student-facing content and **Sapphire Blue** for institution-facing content, unified by **Warm Gold** accents and shared neutrals.

### Core Student Colors

| Role | Color | Hex | Tailwind |
|---|---|---|---|
| Primary | Forest Green | `#2F5D50` | `student` |
| Primary Hover | Deep Forest | `#254A40` | `student-hover` |
| Soft Background | Sage Mist | `#EEF4F1` | `student-mist` |
| Section Background | Soft Moss | `#E3ECE7` | `student-moss` |
| Accent | Warm Gold | `#C89A3D` | `gold` |
| Accent Soft | Pale Gold | `#F3E6C7` | `gold-pale` |
| Headings | Deep Pine | `#1E2E29` | `student-ink` |
| Body Text | Olive Slate | `#5E6B65` | `student-text` |

**Feeling:** Grounded, reassuring, anti-stress, trustworthy.
**Ratio:** 65% neutral/sage, 25% green, 10% gold accent.

### Core School Colors

| Role | Color | Hex | Tailwind |
|---|---|---|---|
| Primary | Sapphire Blue | `#1F4E79` | `school` |
| Primary Hover | Deep Sapphire | `#183C5D` | `school-hover` |
| Soft Background | Ice Blue | `#EFF5FA` | `school-mist` |
| Section Background | Mist Blue | `#E4EDF5` | `school-moss` |
| Accent | Warm Gold | `#C89A3D` | `gold` |
| Accent Soft | Pale Gold | `#F3E6C7` | `gold-pale` |
| Headings | Midnight Blue | `#162535` | `school-ink` |
| Body Text | Steel Slate | `#5D6B78` | `school-text` |

**Feeling:** Structured, capable, polished, institution-safe.
**Ratio:** 70% white/neutral, 20% blue, 10% gold accent.

### Shared Neutrals

| Role | Color | Hex | Tailwind |
|---|---|---|---|
| White | Pure White | `#FFFFFF` | `white` |
| Main Background | Off White | `#FAFBF9` | `offwhite` |
| Border | Soft Stone | `#D9E1DC` | `stone` |
| Light Divider | Mist Gray | `#E9EEEB` | `divider` |
| Dark Text | Charcoal Ink | `#202529` | `charcoal` |
| Secondary Text | Muted Slate | `#667085` | `slate` |

### Shared Gold

| Role | Color | Hex | Tailwind |
|---|---|---|---|
| Brand Accent | Warm Gold | `#C89A3D` | `gold` |
| Hover Accent | Burnished Gold | `#AE8433` | `gold-hover` |
| Soft Accent Bg | Cream Gold | `#F8F1E2` | `gold-soft` |

### CTA Rules

Keep this strict.

**Student CTA:**
- Primary button: Forest Green (`bg-student hover:bg-student-hover text-white`)
- Secondary button: white with green border (`border-student text-student`)
- Gold only for tiny emphasis, never default CTA

**School CTA:**
- Primary button: Sapphire Blue (`bg-school hover:bg-school-hover text-white`)
- Secondary button: white with blue border (`border-school text-school`)
- Gold only for trust accents, premium markers, or highlighted numbers

**Gold should not become the action color. Gold is for value, not navigation.**

### Semantic Colors

| Color | Hex | Usage |
|---|---|---|
| Success | `#059669` (emerald-600) | Completed, accepted, verified |
| Warning | `#D97706` (amber-600) | Deadlines, attention needed |
| Danger | `#DC2626` (red-600) | Errors, rejected, destructive |
| Info | `#0284C7` (sky-600) | Informational, tips |

---

## Typography

**Headings:** Lora (serif) — bold, tracking-tight. Gives warmth and credibility.
**Body:** Inter (sans-serif) — regular, clean, highly readable.

| Element | Font | Weight | Size |
|---|---|---|---|
| Page title | Lora | 700 (bold) | text-2xl+ |
| Section heading | Lora | 600 (semibold) | text-lg |
| Body | Inter | 400 (regular) | text-sm |
| Label | Inter | 500 (medium) | text-sm |
| Caption | Inter | 400 (regular) | text-xs |

---

## Logo

Text-only mark: **Uni**Paith

- "Uni" in Forest Green (`student`) on student pages, Sapphire Blue (`school`) on institution pages
- "Paith" in Charcoal (`charcoal`) bold
- Font: Inter

```jsx
// Student context
<span className="text-student">Uni</span>
<span className="text-charcoal font-extrabold">Paith</span>

// Institution context
<span className="text-school">Uni</span>
<span className="text-charcoal font-extrabold">Paith</span>
```

---

## CTA Rules

### Student CTA
- Primary: Forest Green bg (`bg-student hover:bg-student-hover text-white`)
- Secondary: White with green border (`border-student text-student`)

### School CTA
- Primary: Sapphire Blue bg (`bg-school hover:bg-school-hover text-white`)
- Secondary: White with blue border (`border-school text-school`)

### Gold is NOT a CTA color
Gold is for value, not navigation. Never use it as a button background.

---

## Component Conventions

### Buttons
- Primary student: `bg-student hover:bg-student-hover text-white rounded-xl`
- Primary school: `bg-school hover:bg-school-hover text-white rounded-xl`
- Outline: `border-gray-300 text-charcoal hover:bg-student-mist rounded-xl`
- Ghost: `text-charcoal hover:bg-gray-50`

### Cards
- `bg-white rounded-2xl border border-gray-200`
- Interactive: `hover:shadow-md transition-shadow` (use `hover-lift` utility)

### Badges / Pills
- Student: `bg-student-mist text-student rounded-full`
- School: `bg-school-mist text-school rounded-full`

### Dark Sections
- Background: `bg-charcoal` or `bg-student-ink` / `bg-school-ink`
- Text: `text-white`, secondary: `text-gray-400`
- Accent: `text-student` or `text-school`

### Form Inputs
- Focus ring: `focus:ring-student` (student context) or `focus:ring-school`
- Error: `border-red-500`

---

## Audience Variations

### Student Pages
- Background: `bg-offwhite` or `bg-student-mist`
- More warm tones, more gold micro-accents
- Softer card contrast, fewer dark blocks

### Institution Pages
- Background: `bg-white` or `bg-school-mist`
- More white, sharper contrast
- Clearer data emphasis, more structured layouts

### Shared Pages (Homepage, About, Engine)
- Use both student green and school blue contextually
- Student CTA = green, school CTA = blue
- Neutral dark sections use `bg-charcoal`
