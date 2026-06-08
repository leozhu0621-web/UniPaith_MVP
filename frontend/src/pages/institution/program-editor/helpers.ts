// Spec 23 · Program editor — draft model + hydrate/serialize.
//
// The guided editor (G-I1) edits typed structures, not raw JSON. This module
// owns the translation between the API `Program` (which may carry legacy blob
// shapes from earlier seeds) and the editor's flat, form-friendly `EditorDraft`,
// and back into a `ProgramWritablePayload` of canonical Spec-23 §3 shapes.
import type {
  IntakeRoundForm,
  Program,
  ProgramApplicationRequirements,
  ProgramCostData,
  ProgramOutcomesData,
} from '../../../types'

// ── Select option sets ───────────────────────────────────────────────────────

export const DEGREE_OPTIONS = [
  { value: 'bachelors', label: "Bachelor's" },
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'Ph.D.' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'diploma', label: 'Diploma' },
]

export const DELIVERY_FORMAT_OPTIONS = [
  { value: '', label: 'Not specified' },
  { value: 'in_person', label: 'In person' },
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
]

export const CAMPUS_SETTING_OPTIONS = [
  { value: '', label: 'Not specified' },
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
]

export const TUITION_PERIOD_OPTIONS = [
  { value: 'per_year', label: 'Per year' },
  { value: 'per_credit', label: 'Per credit' },
  { value: 'total_program', label: 'Total program' },
]

export const TEST_STANCE_OPTIONS = [
  { value: 'required', label: 'Required' },
  { value: 'recommended', label: 'Recommended' },
  { value: 'test_optional', label: 'Test-optional' },
  { value: 'test_blind', label: 'Test-blind' },
]

export const REC_TYPE_OPTIONS: { value: 'academic' | 'professional' | 'other'; label: string }[] = [
  { value: 'academic', label: 'Academic' },
  { value: 'professional', label: 'Professional' },
  { value: 'other', label: 'Other' },
]

// Spec 23 §2.8 — promoted-placement categories a program can opt into.
export const PROMOTION_CATEGORY_OPTIONS = [
  { value: 'featured_discovery', label: 'Featured in Discovery' },
  { value: 'subject_spotlight', label: 'Subject spotlight' },
  { value: 'scholarship_highlight', label: 'Scholarship highlight' },
  { value: 'deadline_reminder', label: 'Deadline reminders' },
  { value: 'open_house', label: 'Open house & events' },
  { value: 'international_focus', label: 'International applicants' },
]

// The 8 sections (Spec 23 §2) — drives the side rail + scroll-to-section on
// publish-validation errors. `id` doubles as the section element's DOM id.
export const SECTIONS = [
  { id: 'identity', label: 'Identity' },
  { id: 'overview', label: 'Overview & structure' },
  { id: 'requirements', label: 'Requirements' },
  { id: 'english', label: 'English proficiency' },
  { id: 'deadlines', label: 'Deadlines & rounds' },
  { id: 'costs', label: 'Costs' },
  { id: 'outcomes', label: 'Outcomes' },
  { id: 'media', label: 'Media' },
  { id: 'promotion', label: 'Promotion settings' },
] as const

export type SectionId = (typeof SECTIONS)[number]['id']

// ── Draft shape ──────────────────────────────────────────────────────────────

export interface EditorDraft {
  // Identity
  program_name: string
  school_id: string
  department: string
  degree_type: string
  delivery_format: string
  campus_setting: string
  duration_months: string
  // Overview & structure
  description_text: string
  tracks_concentrations: string[]
  tracks_note: string
  learning_format: string
  who_its_for: string
  highlights: string[]
  faculty_contacts: { name: string; email: string; role: string }[]
  // Preserved non-array (dict) faculty payload (e.g. { lead, note, directory_url })
  // that the form can't edit — kept so saving other fields never wipes curated data.
  faculty_contacts_dict: Record<string, any> | null
  // Requirements
  application_requirements: ProgramApplicationRequirements
  requirements_kv: { key: string; value: string }[]
  acceptance_rate_pct: string
  // English proficiency (Spec 38 §2.2)
  english_policy: EnglishPolicyForm
  // Deadlines & rounds
  intake_rounds: IntakeRoundForm[]
  application_deadline: string
  program_start_date: string
  // Costs
  cost_data: ProgramCostData
  // Outcomes
  outcomes_data: ProgramOutcomesData
  // Media
  media_urls: string[]
  // Promotion
  promotion_categories: string[]
}

// English proficiency policy (Spec 38 §2.2) — accepted tests + minimum scores +
// waiver rules. Stored on `programs.english_policy`.
export interface EnglishPolicyForm {
  accepted_tests: { test: string; min_score: string }[]
  waiver_native_english_countries: string[]
  waiver_prior_degree_in_english: boolean
}

export const ENGLISH_TEST_OPTIONS = [
  { value: 'TOEFL', label: 'TOEFL' },
  { value: 'IELTS', label: 'IELTS' },
  { value: 'DET', label: 'Duolingo (DET)' },
  { value: 'PTE', label: 'PTE' },
]

export function defaultEnglishPolicy(): EnglishPolicyForm {
  return {
    accepted_tests: [],
    waiver_native_english_countries: [],
    waiver_prior_degree_in_english: true,
  }
}

// ── Default factories ────────────────────────────────────────────────────────

export function defaultAppReqs(): ProgramApplicationRequirements {
  return {
    materials: [],
    prerequisites: [],
    test_policy: {
      stance: 'test_optional',
      required: [],
      optional: [],
      accepted_tests: [],
      superscore_enabled: false,
      waived_rules: '',
      typical_ranges: [],
    },
    recommendations: { required_count: 0, types: [] },
  }
}

export function defaultCostData(): ProgramCostData {
  return {
    tuition_amount: null,
    tuition_currency: 'USD',
    tuition_period: 'per_year',
    fees: [],
    estimated_total_cost_band: { min: null, max: null, currency: 'USD' },
    funding_signals: {
      ta_funded: false,
      ra_funded: false,
      merit_scholarship_available: false,
      need_based_available: false,
    },
  }
}

export function defaultOutcomes(): ProgramOutcomesData {
  return {
    placement_rate_pct: null,
    median_starting_salary: null,
    salary_distribution_bands: [],
    common_roles: [],
    top_employers: [],
    internship_to_offer_pct: null,
    time_to_placement_months: null,
    outcome_reporting_window: '',
  }
}

let _ridCounter = 0
export function rid(): string {
  try {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  } catch {
    /* fall through */
  }
  _ridCounter += 1
  return `round-${_ridCounter}-${performance.now()}`
}

export function emptyRound(): IntakeRoundForm {
  return {
    id: rid(),
    name: '',
    term: { season: '', year: new Date().getFullYear() + 1 },
    open_date: null,
    deadline: null,
    decision_date: null,
    start_date: null,
    capacity: null,
  }
}

// ── Coercion helpers ─────────────────────────────────────────────────────────

const isObj = (v: unknown): v is Record<string, any> =>
  !!v && typeof v === 'object' && !Array.isArray(v)
const arr = <T>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : [])
const str = (v: unknown): string => (v == null ? '' : String(v))
const numOrNull = (v: unknown): number | null =>
  v == null || v === '' || Number.isNaN(Number(v)) ? null : Number(v)

// employment/placement may arrive as a fraction (0–1) or a percent (0–100).
function pctNorm(v: unknown): number | null {
  const n = numOrNull(v)
  if (n == null) return null
  return n > 0 && n <= 1 ? Math.round(n * 1000) / 10 : n
}

function prettify(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function parseTerm(key: string): { season: string; year: number } {
  // "fall_2026" → { season: "Fall", year: 2026 }
  const m = /([a-zA-Z]+)[_\s-]*(\d{4})/.exec(key)
  if (m) return { season: prettify(m[1]), year: Number(m[2]) }
  return { season: prettify(key), year: new Date().getFullYear() + 1 }
}

// ── Hydrate: Program → EditorDraft ───────────────────────────────────────────

function hydrateAppReqs(raw: unknown): ProgramApplicationRequirements {
  const base = defaultAppReqs()
  if (Array.isArray(raw)) {
    // Legacy: flat checklist [{label, required, note}] → materials.
    base.materials = raw
      .filter(isObj)
      .map(m => ({ name: str(m.name ?? m.label), required: !!m.required, note: str(m.note) || undefined }))
    return base
  }
  if (isObj(raw)) {
    return {
      materials: arr<Record<string, any>>(raw.materials).map(m => ({
        name: str(m.name ?? m.label),
        required: !!m.required,
        note: str(m.note) || undefined,
      })),
      prerequisites: arr<Record<string, any>>(raw.prerequisites).map(p => ({
        name: str(p.name),
        required: !!p.required,
        allowed_substitutes: arr<string>(p.allowed_substitutes).map(str),
      })),
      test_policy: {
        stance: (raw.test_policy?.stance as any) ?? base.test_policy.stance,
        required: arr<string>(raw.test_policy?.required).map(str),
        optional: arr<string>(raw.test_policy?.optional).map(str),
        accepted_tests: arr<string>(raw.test_policy?.accepted_tests).map(str),
        superscore_enabled: !!raw.test_policy?.superscore_enabled,
        waived_rules: str(raw.test_policy?.waived_rules),
        typical_ranges: arr<Record<string, any>>(raw.test_policy?.typical_ranges).map(t => ({
          test: str(t.test),
          low: Number(t.low) || 0,
          high: Number(t.high) || 0,
        })),
      },
      recommendations: {
        required_count: Number(raw.recommendations?.required_count) || 0,
        types: arr<any>(raw.recommendations?.types),
      },
    }
  }
  return base
}

function hydrateRounds(raw: unknown): IntakeRoundForm[] {
  if (Array.isArray(raw)) {
    return raw.filter(isObj).map(r => ({
      id: str(r.id) || rid(),
      name: str(r.name ?? r.round_name),
      term: isObj(r.term)
        ? { season: str(r.term.season), year: Number(r.term.year) || new Date().getFullYear() + 1 }
        : parseTerm(str(r.intake_term)),
      open_date: r.open_date ?? r.application_open ?? null,
      deadline: r.deadline ?? r.application_deadline ?? null,
      decision_date: r.decision_date ?? null,
      start_date: r.start_date ?? r.program_start ?? null,
      capacity: numOrNull(r.capacity),
    }))
  }
  if (isObj(raw)) {
    // Legacy dict: { fall_2026: { early_decision_1: { deadline }, ... }, source }
    const rounds: IntakeRoundForm[] = []
    for (const [termKey, termVal] of Object.entries(raw)) {
      if (termKey === 'source' || !isObj(termVal)) continue
      const term = parseTerm(termKey)
      for (const [roundKey, roundVal] of Object.entries(termVal)) {
        if (roundKey === 'term' || roundKey === 'enrollment_deadline' || !isObj(roundVal)) continue
        rounds.push({
          id: rid(),
          name: prettify(roundKey),
          term,
          open_date: (roundVal as any).open_date ?? null,
          deadline: (roundVal as any).deadline ?? null,
          decision_date: (roundVal as any).decision_date ?? (roundVal as any).notification ?? null,
          start_date: (roundVal as any).start_date ?? null,
          capacity: numOrNull((roundVal as any).capacity),
        })
      }
    }
    return rounds
  }
  return []
}

function hydrateCost(raw: unknown): ProgramCostData {
  const base = defaultCostData()
  if (!isObj(raw)) return base
  let fees = base.fees
  if (Array.isArray(raw.fees)) {
    fees = raw.fees.filter(isObj).map(f => ({
      name: str(f.name),
      amount: Number(f.amount) || 0,
      required: !!f.required,
    }))
  } else if (isObj(raw.fees)) {
    fees = Object.entries(raw.fees).map(([name, amount]) => ({
      name: prettify(name),
      amount: Number(amount) || 0,
      required: false,
    }))
  }
  return {
    tuition_amount: numOrNull(raw.tuition_amount ?? raw.tuition_annual ?? raw.tuition_annual_institution),
    tuition_currency: str(raw.tuition_currency) || 'USD',
    tuition_period: (raw.tuition_period as any) ?? 'per_year',
    fees,
    estimated_total_cost_band: {
      min: numOrNull(raw.estimated_total_cost_band?.min),
      max: numOrNull(raw.estimated_total_cost_band?.max ?? raw.total_cost_attendance),
      currency: str(raw.estimated_total_cost_band?.currency) || 'USD',
    },
    funding_signals: {
      ta_funded: !!raw.funding_signals?.ta_funded,
      ra_funded: !!raw.funding_signals?.ra_funded,
      merit_scholarship_available: !!raw.funding_signals?.merit_scholarship_available,
      need_based_available: !!raw.funding_signals?.need_based_available,
    },
  }
}

function hydrateOutcomes(raw: unknown): ProgramOutcomesData {
  const base = defaultOutcomes()
  if (!isObj(raw)) return base
  return {
    placement_rate_pct: raw.placement_rate_pct != null ? numOrNull(raw.placement_rate_pct) : pctNorm(raw.employment_rate),
    median_starting_salary: numOrNull(raw.median_starting_salary ?? raw.median_salary),
    salary_distribution_bands: arr<Record<string, any>>(raw.salary_distribution_bands).map(b => ({
      band_label: str(b.band_label),
      percent: Number(b.percent) || 0,
    })),
    common_roles: arr<string>(raw.common_roles).map(str),
    top_employers: arr<string>(raw.top_employers).map(str),
    internship_to_offer_pct:
      raw.internship_to_offer_pct != null
        ? numOrNull(raw.internship_to_offer_pct)
        : pctNorm(raw.internship_conversion_rate),
    time_to_placement_months: numOrNull(raw.time_to_placement_months),
    outcome_reporting_window: str(raw.outcome_reporting_window ?? raw.employment_timeframe),
  }
}

export function fromProgram(p: Program): EditorDraft {
  const t = p.tracks
  let concentrations: string[] = []
  let tracksNote = ''
  let learningFormat = ''
  if (Array.isArray(t)) concentrations = t.map(str)
  else if (isObj(t)) {
    concentrations = arr<string>((t as any).concentrations).map(str)
    tracksNote = str((t as any).note)
    learningFormat = str((t as any).learning_format)
  }
  return {
    program_name: str(p.program_name),
    school_id: str(p.school_id),
    department: str(p.department),
    degree_type: str(p.degree_type),
    delivery_format: str(p.delivery_format),
    campus_setting: str(p.campus_setting),
    duration_months: p.duration_months != null ? String(p.duration_months) : '',
    description_text: str(p.description_text),
    tracks_concentrations: concentrations.length ? concentrations : [],
    tracks_note: tracksNote,
    learning_format: learningFormat,
    who_its_for: str(p.who_its_for),
    highlights: arr<string>(p.highlights).map(str),
    faculty_contacts: arr<Record<string, any>>(p.faculty_contacts).map(f => ({
      name: str(f.name),
      email: str(f.email),
      role: str(f.role),
    })),
    faculty_contacts_dict: isObj(p.faculty_contacts) ? p.faculty_contacts : null,
    application_requirements: hydrateAppReqs(p.application_requirements),
    english_policy: {
      accepted_tests: arr<Record<string, any>>(p.english_policy?.accepted_tests).map(t => ({
        test: str(t.test),
        min_score: t.min_score != null ? String(t.min_score) : '',
      })),
      waiver_native_english_countries: arr<string>(
        p.english_policy?.waiver_native_english_countries,
      ).map(str),
      waiver_prior_degree_in_english: p.english_policy?.waiver_prior_degree_in_english ?? true,
    },
    requirements_kv: isObj(p.requirements)
      ? Object.entries(p.requirements).map(([key, value]) => ({ key, value: str(value) }))
      : [],
    acceptance_rate_pct: p.acceptance_rate != null ? String(Math.round(Number(p.acceptance_rate) * 1000) / 10) : '',
    intake_rounds: hydrateRounds(p.intake_rounds),
    application_deadline: str(p.application_deadline).split('T')[0],
    program_start_date: str(p.program_start_date).split('T')[0],
    cost_data: hydrateCost(p.cost_data),
    outcomes_data: hydrateOutcomes(p.outcomes_data),
    media_urls: arr<string>(p.media_urls).map(str),
    promotion_categories: arr<string>(p.promotion_categories).map(str),
  }
}

export function emptyDraft(): EditorDraft {
  return {
    program_name: '',
    school_id: '',
    department: '',
    degree_type: '',
    delivery_format: '',
    campus_setting: '',
    duration_months: '',
    description_text: '',
    tracks_concentrations: [],
    tracks_note: '',
    learning_format: '',
    who_its_for: '',
    highlights: [],
    faculty_contacts: [],
    faculty_contacts_dict: null,
    application_requirements: defaultAppReqs(),
    english_policy: defaultEnglishPolicy(),
    requirements_kv: [],
    acceptance_rate_pct: '',
    intake_rounds: [],
    application_deadline: '',
    program_start_date: '',
    cost_data: defaultCostData(),
    outcomes_data: defaultOutcomes(),
    media_urls: [],
    promotion_categories: [],
  }
}

// ── Serialize: EditorDraft → API payload ─────────────────────────────────────

const clean = (s: string[]) => s.map(v => v.trim()).filter(Boolean)

export function toPayload(d: EditorDraft): Record<string, any> {
  const concentrations = clean(d.tracks_concentrations)
  const tracks =
    concentrations.length || d.tracks_note.trim() || d.learning_format.trim()
      ? {
          concentrations,
          ...(d.tracks_note.trim() ? { note: d.tracks_note.trim() } : {}),
          ...(d.learning_format.trim() ? { learning_format: d.learning_format.trim() } : {}),
        }
      : undefined

  const requirements = d.requirements_kv.reduce<Record<string, string>>((acc, r) => {
    if (r.key.trim()) acc[r.key.trim()] = r.value
    return acc
  }, {})

  const appReqs: ProgramApplicationRequirements = {
    materials: d.application_requirements.materials.filter(m => m.name.trim()),
    prerequisites: d.application_requirements.prerequisites.filter(p => p.name.trim()),
    test_policy: {
      ...d.application_requirements.test_policy,
      required: clean(d.application_requirements.test_policy.required),
      optional: clean(d.application_requirements.test_policy.optional),
      accepted_tests: clean(d.application_requirements.test_policy.accepted_tests),
      typical_ranges: d.application_requirements.test_policy.typical_ranges.filter(t => t.test.trim()),
    },
    recommendations: d.application_requirements.recommendations,
  }

  const englishPolicy = {
    accepted_tests: d.english_policy.accepted_tests
      .filter(t => t.test.trim())
      .map(t => ({ test: t.test, min_score: numOrNull(t.min_score) ?? 0 })),
    waiver_native_english_countries: clean(d.english_policy.waiver_native_english_countries),
    waiver_prior_degree_in_english: d.english_policy.waiver_prior_degree_in_english,
  }

  const intakeRounds = d.intake_rounds
    .filter(r => r.name.trim() || r.deadline)
    .map(r => ({ ...r, capacity: r.capacity }))

  const cost: ProgramCostData = {
    ...d.cost_data,
    fees: d.cost_data.fees.filter(f => f.name.trim()),
  }

  const outcomes: ProgramOutcomesData = {
    ...d.outcomes_data,
    common_roles: clean(d.outcomes_data.common_roles),
    top_employers: clean(d.outcomes_data.top_employers),
    salary_distribution_bands: d.outcomes_data.salary_distribution_bands.filter(b => b.band_label.trim()),
  }

  const acceptanceRate = numOrNull(d.acceptance_rate_pct)

  // Form edits the array shape; when it's empty fall back to any preserved
  // non-array (dict) payload so saving never wipes curated faculty data.
  const facultyContacts = d.faculty_contacts.filter(f => f.name.trim())

  return {
    program_name: d.program_name.trim(),
    degree_type: d.degree_type,
    school_id: d.school_id || null,
    department: d.department.trim() || undefined,
    delivery_format: d.delivery_format || undefined,
    campus_setting: d.campus_setting || undefined,
    duration_months: d.duration_months ? Number(d.duration_months) : undefined,
    description_text: d.description_text.trim() || undefined,
    who_its_for: d.who_its_for.trim() || undefined,
    tracks,
    highlights: clean(d.highlights),
    faculty_contacts: facultyContacts.length ? facultyContacts : d.faculty_contacts_dict ?? facultyContacts,
    application_requirements: appReqs,
    english_policy: englishPolicy,
    requirements: Object.keys(requirements).length ? requirements : undefined,
    acceptance_rate: acceptanceRate != null ? acceptanceRate / 100 : undefined,
    intake_rounds: intakeRounds,
    application_deadline: d.application_deadline || undefined,
    program_start_date: d.program_start_date || undefined,
    cost_data: cost,
    // Keep the top-level annual tuition column in sync so the student card,
    // search, and detail page (which read `program.tuition` first) reflect edits.
    tuition: cost.tuition_period === 'per_year' && cost.tuition_amount != null ? cost.tuition_amount : undefined,
    outcomes_data: outcomes,
    media_urls: clean(d.media_urls),
    promotion_categories: d.promotion_categories,
  }
}
