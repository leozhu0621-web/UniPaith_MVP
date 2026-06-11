// Spec 23 ↔ Spec 11 bridge.
//
// The institution editor (Spec 23 §3) writes *canonical* structured blobs:
//   cost_data.tuition_amount / fees[] / estimated_total_cost_band
//   outcomes_data.median_starting_salary / placement_rate_pct (0–100) / …
//   application_requirements.materials[] / prerequisites / test_policy
//   intake_rounds[]  (array of {name, term, deadline, …})
//
// The student program detail page (Spec 11) was built against the earlier
// *legacy* blob shapes (cost_data.tuition_annual, fees as a dict, outcomes_data
// .median_salary, employment_rate as a 0–1 fraction, intake_rounds as a dict).
// These helpers project canonical → the legacy-compatible shape the page already
// renders, while passing legacy keys through untouched — so existing seeds and
// freshly-edited programs both render. Canonical wins; legacy is the fallback.

const isObj = (v: unknown): v is Record<string, any> =>
  !!v && typeof v === 'object' && !Array.isArray(v)

const arr = <T>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : [])

const num = (v: unknown): number | null =>
  v == null || v === '' || Number.isNaN(Number(v)) ? null : Number(v)

// A percent (0–100) → the 0–1 fraction the student page multiplies by 100.
const pctToFraction = (v: unknown): number | null => {
  const n = num(v)
  return n == null ? null : n / 100
}

export function normalizeCostData(raw: unknown): Record<string, any> {
  if (!isObj(raw)) return {}
  // fees → dict { label: amount } for the legacy `Object.entries(fees)` render.
  let feesDict: Record<string, number> = {}
  if (Array.isArray(raw.fees)) {
    for (const f of raw.fees) {
      if (isObj(f) && f.name) feesDict[String(f.name)] = Number(f.amount) || 0
    }
  } else if (isObj(raw.fees)) {
    feesDict = raw.fees as Record<string, number>
  }
  const band = isObj(raw.estimated_total_cost_band) ? raw.estimated_total_cost_band : {}
  return {
    ...raw,
    // tuition_annual is the key the page's effective-tuition fallback reads.
    tuition_annual: num(raw.tuition_amount ?? raw.tuition_annual ?? raw.tuition_annual_institution),
    fees: feesDict,
    total_cost_attendance: num(raw.total_cost_attendance ?? (band as any).max),
  }
}

export function normalizeOutcomes(raw: unknown): Record<string, any> {
  if (!isObj(raw)) return {}
  return {
    ...raw,
    median_salary: num(raw.median_starting_salary ?? raw.median_salary),
    // placement_rate_pct is a percent; the page renders employment_rate × 100.
    employment_rate:
      raw.placement_rate_pct != null ? pctToFraction(raw.placement_rate_pct) : num(raw.employment_rate),
    internship_conversion_rate:
      raw.internship_to_offer_pct != null
        ? pctToFraction(raw.internship_to_offer_pct)
        : num(raw.internship_conversion_rate),
    // The student page renders "Within {timeframe}"; strip a leading "Within "
    // from the reporting window so it doesn't read "Within Within …".
    employment_timeframe:
      String(raw.outcome_reporting_window || raw.employment_timeframe || '').replace(/^within\s+/i, '') ||
      undefined,
    top_employers: Array.isArray(raw.top_employers) ? raw.top_employers : [],
    // The student Outcomes tab surfaces an "Industry Placement" panel; the
    // editor captures common_roles, so fall back to those when no industries set.
    top_industries: Array.isArray(raw.top_industries)
      ? raw.top_industries
      : Array.isArray(raw.common_roles)
        ? raw.common_roles
        : [],
  }
}

// Application requirements → the flat checklist the Admissions tab renders.
// Accepts the canonical {materials:[{name,required,note}], …} object OR the
// legacy [{label,required,note}] array.
export function normalizeRequirements(
  raw: unknown,
): Array<{ label: string; required?: boolean; note?: string }> {
  const fromItem = (m: Record<string, any>) => ({
    label: String(m.name ?? m.label ?? ''),
    required: m.required,
    note: m.note,
  })
  if (Array.isArray(raw)) return raw.filter(isObj).map(fromItem).filter(r => r.label)
  if (isObj(raw) && Array.isArray(raw.materials))
    return raw.materials.filter(isObj).map(fromItem).filter((r: any) => r.label)
  return []
}

// Earliest deadline from a canonical intake_rounds[] (headline fallback).
export function intakeDeadlineFromArray(arr: unknown): string | null {
  if (!Array.isArray(arr)) return null
  const dated = arr
    .filter(isObj)
    .map(r => (r as any).deadline)
    .filter((d): d is string => !!d)
    .sort()
  return dated[0] ?? null
}

// Canonical intake_rounds[] → the {term, rounds, enrollment_deadline} the
// admissions timeline renders (rounds need name + deadline + decision_release).
export function intakeTimelineFromArray(
  arr: unknown,
): { term: string; rounds: any[]; enrollment_deadline: string | null } | null {
  if (!Array.isArray(arr)) return null
  const rounds = arr
    .filter(isObj)
    .filter(r => (r as any).deadline)
    .map(r => {
      const x = r as any
      return {
        name: String(x.name || 'Application round'),
        deadline: x.deadline,
        decision_release: x.decision_date ?? null,
        start_date: x.start_date ?? null,
        binding: false,
      }
    })
  if (rounds.length === 0) return null
  const first = arr.find(isObj) as any
  const term =
    first && isObj(first.term) && first.term.season
      ? `${first.term.season} ${first.term.year ?? ''}`.trim()
      : 'Upcoming intake'
  return { term, rounds, enrollment_deadline: null }
}

// Tracks / concentrations metadata from the Spec 23 editor (tracks object or array).
export function extractTracksMeta(tracks: unknown): {
  concentrations: string[]
  note: string
  learning_format: string
  curriculum: Array<{ term: string; courses: string[] }>
} {
  const out = {
    concentrations: [] as string[],
    note: '',
    learning_format: '',
    curriculum: [] as Array<{ term: string; courses: string[] }>,
  }
  if (Array.isArray(tracks)) {
    out.concentrations = tracks.filter(t => typeof t === 'string') as string[]
  } else if (isObj(tracks)) {
    for (const key of ['concentrations', 'tracks', 'subfields', 'specializations', 'items']) {
      if (Array.isArray(tracks[key])) {
        // entries are plain strings or {name} objects (the data-module shape)
        out.concentrations = (tracks[key] as unknown[])
          .map(t => (typeof t === 'string' ? t : isObj(t) ? String(t.name ?? '') : ''))
          .filter(Boolean)
        break
      }
    }
    out.note = String(tracks.note || '')
    out.learning_format = String(tracks.learning_format || '')
    if (Array.isArray(tracks.curriculum)) {
      out.curriculum = (tracks.curriculum as unknown[])
        .filter(isObj)
        .map(t => ({
          term: String((t as Record<string, any>).term ?? ''),
          courses: arr<string>((t as Record<string, any>).courses).map(String).filter(Boolean),
        }))
        .filter(t => t.term && t.courses.length > 0)
    }
  }
  return out
}

export function extractPrerequisites(
  raw: unknown,
): Array<{ name: string; required: boolean; allowed_substitutes: string[] }> {
  if (!isObj(raw)) return []
  return arr<Record<string, any>>(raw.prerequisites)
    .map(p => ({
      name: String(p.name ?? ''),
      required: p.required !== false,
      allowed_substitutes: arr<string>(p.allowed_substitutes).map(String),
    }))
    .filter(p => p.name)
}

const TEST_STANCE_LABELS: Record<string, string> = {
  required: 'Required',
  recommended: 'Recommended',
  test_optional: 'Test-optional',
  test_blind: 'Test-blind',
}

export function extractTestPolicy(raw: unknown): {
  stance: string
  stance_label: string
  required: string[]
  optional: string[]
  accepted_tests: string[]
  superscore_enabled: boolean
  waived_rules: string
  typical_ranges: Array<{ test: string; low: number; high: number }>
} | null {
  if (!isObj(raw) || !isObj(raw.test_policy)) return null
  const tp = raw.test_policy
  const stance = String(tp.stance || '')
  const required = arr<string>(tp.required).map(String).filter(Boolean)
  const optional = arr<string>(tp.optional).map(String).filter(Boolean)
  const accepted = arr<string>(tp.accepted_tests).map(String).filter(Boolean)
  const ranges = arr<Record<string, any>>(tp.typical_ranges)
    .filter(t => t.test)
    .map(t => ({ test: String(t.test), low: Number(t.low) || 0, high: Number(t.high) || 0 }))
  const waived = String(tp.waived_rules || '')
  const hasContent =
    stance || required.length || optional.length || accepted.length || ranges.length || waived
  if (!hasContent) return null
  return {
    stance,
    stance_label: TEST_STANCE_LABELS[stance] || stance.replace(/_/g, ' '),
    required,
    optional,
    accepted_tests: accepted,
    superscore_enabled: !!tp.superscore_enabled,
    waived_rules: waived,
    typical_ranges: ranges,
  }
}

export function extractRecommendations(raw: unknown): { required_count: number; types: string[] } | null {
  if (!isObj(raw) || !isObj(raw.recommendations)) return null
  const count = Number(raw.recommendations.required_count) || 0
  const types = arr<string>(raw.recommendations.types).map(String).filter(Boolean)
  if (count <= 0 && types.length === 0) return null
  return { required_count: count, types }
}

export function extractFundingSignals(raw: unknown): Record<string, boolean> | null {
  if (!isObj(raw) || !isObj(raw.funding_signals)) return null
  const fs = raw.funding_signals as Record<string, boolean>
  if (!Object.values(fs).some(Boolean)) return null
  return fs
}

export function extractSalaryBands(raw: unknown): Array<{ band_label: string; percent: number }> {
  if (!isObj(raw)) return []
  return arr<Record<string, any>>(raw.salary_distribution_bands)
    .filter(b => b.band_label)
    .map(b => ({ band_label: String(b.band_label), percent: Number(b.percent) || 0 }))
}
