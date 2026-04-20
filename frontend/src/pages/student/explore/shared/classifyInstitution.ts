/**
 * classifyInstitution — derive a type classification from description_text
 * + the institution's `type` field, returning a normalized code + label.
 *
 * The DB's `type` column today is usually just "university" for every school,
 * which isn't useful for filtering. Parse the description for phrases that
 * actually describe the school's character (private research, liberal arts,
 * community college, etc.) and expose both a code (for URL filter values)
 * and a display label (for pills and dropdowns).
 */

export type InstitutionClassification =
  | 'private_research'
  | 'public_research'
  | 'liberal_arts'
  | 'community'
  | 'private_university'
  | 'public_university'
  | 'other'

export interface ClassificationResult {
  code: InstitutionClassification
  label: string
}

const CLASS_DEFS: Array<{ code: InstitutionClassification; label: string; patterns: RegExp[] }> = [
  {
    code: 'private_research',
    label: 'Private Research',
    patterns: [/\bprivate research\b/i, /\bprivately.funded research\b/i],
  },
  {
    code: 'public_research',
    label: 'Public Research',
    patterns: [/\bpublic research\b/i, /\bstate research\b/i, /\bflagship\b/i],
  },
  {
    code: 'liberal_arts',
    label: 'Liberal Arts',
    patterns: [/\bliberal arts college\b/i, /\bliberal.arts\b.*\bcollege\b/i],
  },
  {
    code: 'community',
    label: 'Community',
    patterns: [/\bcommunity college\b/i, /\btwo.year college\b/i, /\bjunior college\b/i],
  },
  {
    code: 'private_university',
    label: 'Private',
    patterns: [/\bprivate university\b/i, /\bprivate\b(?!.*research)/i],
  },
  {
    code: 'public_university',
    label: 'Public',
    patterns: [/\bpublic university\b/i, /\bstate university\b/i, /\bstate college\b/i],
  },
]

/**
 * Return a classification given the institution's description and type hint.
 * Runs the regexes in priority order so that more specific classifications
 * (private research, liberal arts) win over broader ones (private).
 */
export function classifyInstitution(input: {
  description_text?: string | null
  type?: string | null
}): ClassificationResult {
  const text = (input.description_text || '').trim()
  for (const def of CLASS_DEFS) {
    if (def.patterns.some(re => re.test(text))) {
      return { code: def.code, label: def.label }
    }
  }
  // Fallbacks based on the raw `type` column.
  const t = (input.type || '').toLowerCase()
  if (t === 'college') return { code: 'liberal_arts', label: 'College' }
  if (t === 'community_college') return { code: 'community', label: 'Community' }
  if (t === 'university') return { code: 'other', label: 'University' }
  return { code: 'other', label: input.type ? input.type.replace(/_/g, ' ') : 'Institution' }
}

/** All filterable classification codes + labels, used to build the Type filter dropdown. */
export const CLASSIFICATION_OPTIONS: ClassificationResult[] = [
  { code: 'private_research', label: 'Private Research' },
  { code: 'public_research', label: 'Public Research' },
  { code: 'liberal_arts', label: 'Liberal Arts' },
  { code: 'private_university', label: 'Private' },
  { code: 'public_university', label: 'Public' },
  { code: 'community', label: 'Community' },
]

/**
 * Bin a student body size into a welcoming-label size bucket.
 * Still used on the university card (as context), even though the Size
 * filter itself was removed.
 */
export type SizeBucket = 'small' | 'medium' | 'large'

export function sizeBucket(studentBodySize?: number | null): SizeBucket | null {
  if (!studentBodySize || studentBodySize <= 0) return null
  if (studentBodySize < 5000) return 'small'
  if (studentBodySize < 20000) return 'medium'
  return 'large'
}

export const SIZE_OPTIONS: Array<{ code: SizeBucket; label: string; hint: string }> = [
  { code: 'small', label: 'Small', hint: 'Under 5K' },
  { code: 'medium', label: 'Medium', hint: '5K – 20K' },
  { code: 'large', label: 'Large', hint: '20K+' },
]

/** Title-case a campus setting string ("urban" → "Urban"). */
export function formatSetting(s?: string | null): string | null {
  if (!s) return null
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()
}

/* ── Degree levels and delivery formats (filter options) ───────────────── */

export const DEGREE_LEVEL_OPTIONS: Array<{ code: string; label: string }> = [
  { code: 'bachelors', label: "Bachelor's" },
  { code: 'masters', label: "Master's" },
  { code: 'phd', label: 'PhD' },
  { code: 'doctorate', label: 'Doctorate' },
  { code: 'certificate', label: 'Certificate' },
  { code: 'associate', label: 'Associate' },
]

export const DELIVERY_FORMAT_OPTIONS: Array<{ code: string; label: string }> = [
  { code: 'on_campus', label: 'On Campus' },
  { code: 'online', label: 'Online' },
  { code: 'hybrid', label: 'Hybrid' },
  { code: 'in_person', label: 'In-Person' },
]

/* ── SAT tiers ──────────────────────────────────────────────────────────── */

export type SatTier = 'under_1200' | '1200_1400' | '1400_1500' | '1500_plus'

export function satTier(sat?: number | null): SatTier | null {
  if (!sat || sat <= 0) return null
  if (sat < 1200) return 'under_1200'
  if (sat < 1400) return '1200_1400'
  if (sat < 1500) return '1400_1500'
  return '1500_plus'
}

export const SAT_OPTIONS: Array<{ code: SatTier; label: string }> = [
  { code: '1500_plus', label: 'SAT 1500+' },
  { code: '1400_1500', label: 'SAT 1400–1500' },
  { code: '1200_1400', label: 'SAT 1200–1400' },
  { code: 'under_1200', label: 'SAT under 1200' },
]

/* ── Tuition tiers ──────────────────────────────────────────────────────── */

export type TuitionTier = 'under_20k' | '20_40k' | '40_60k' | '60_plus'

export function tuitionTier(tuition?: number | null): TuitionTier | null {
  if (!tuition || tuition <= 0) return null
  if (tuition < 20000) return 'under_20k'
  if (tuition < 40000) return '20_40k'
  if (tuition < 60000) return '40_60k'
  return '60_plus'
}

export const TUITION_OPTIONS: Array<{ code: TuitionTier; label: string }> = [
  { code: 'under_20k', label: 'Under $20K / yr' },
  { code: '20_40k', label: '$20K – $40K / yr' },
  { code: '40_60k', label: '$40K – $60K / yr' },
  { code: '60_plus', label: '$60K+ / yr' },
]
