// Spec 43 — Major-Specific Field Catalog wire types.
// Mirror of unipaith-backend/src/unipaith/schemas/major_specific.py +
// services/major_track_catalog.py (the field-schema shape) +
// ai/major_track_coach.py (the §4.18 coach overlay).

export type ReadinessBand = 'low' | 'medium' | 'high'
export type FieldKind = 'rating_1_5' | 'enum' | 'tags' | 'bool' | 'number' | 'link' | 'text'

export interface CatalogField {
  key: string
  label: string
  kind: FieldKind
  max?: number
  options?: string[]
  unit?: string
}

export interface CatalogGroup {
  key: string
  label: string
  fields: CatalogField[]
}

export interface TrackSchema {
  track_key: string
  label: string
  blurb: string
  groups: CatalogGroup[]
}

export interface CatalogResponse {
  tracks: TrackSchema[]
  suggested_tracks: string[]
}

export type TrackSignalValue = number | boolean | string | string[]
export type TrackSignals = Record<string, TrackSignalValue>

export interface CoachGap {
  key: string
  label: string
  value: number | null
  state: 'weak' | 'unrated'
}

export interface TrackCoach {
  track_key: string
  major_track_fit_score: number
  completeness: number
  readiness_band: ReadinessBand
  coding_readiness_band?: ReadinessBand
  project_coverage_map: Record<string, number>
  skill_gap_severity: 'none' | 'low' | 'medium' | 'high'
  specialization_match_tags: string[]
  gaps: CoachGap[]
  suggested_artifacts_to_add: string[]
  track_recommendation: string | null
  suggested_bridge_plan: string
}

export interface TrackSignalsOut {
  track_key: string
  label: string
  signals: TrackSignals
  source: string
  confidence: number
  record_version: number
  updated_at: string | null
  coach: TrackCoach | null
}

export interface TracksResponse {
  active_tracks: string[]
  suggested_tracks: string[]
  tracks: TrackSignalsOut[]
}

export interface MajorSpecificSummary {
  active_track_count: number
  inference_enabled: boolean
  primary_track: string | null
  major_track_fit_score_per_target_track: Record<string, number> | null
  tracks: TrackCoach[] | null
}
