// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === POSTS ===
// Spec 27 §2.4 — a call-to-action attached to a post.
export type PostCTAType =
  | 'view_program'
  | 'rsvp'
  | 'request_info'
  | 'start_application'
  | 'add_to_calendar'

export interface PostCTA {
  type: PostCTAType
  label: string
  target?: string | null
}

// Spec 27 §2.3 — visibility scope for a post.
export interface PostVisibility {
  public: boolean
  segment_ids: string[]
  region_scopes: string[]
}

export interface InstitutionPost {
  id: string
  institution_id: string
  author_id: string | null
  title: string
  body: string
  media_urls: { url: string; type: string; caption?: string }[] | null
  pinned: boolean
  tagged_program_ids: string[] | null
  tagged_intake: string | null
  status: 'draft' | 'published' | 'scheduled' | 'archived'
  scheduled_for: string | null
  published_at: string | null
  // Channel-sourcing provenance — 'manual' (school-authored) vs 'news_rss' etc.
  source?: string
  source_url?: string | null
  image_url?: string | null
  // Scope tags for school/program-specific updates.
  school_id?: string | null
  program_id?: string | null
  is_template: boolean
  template_name: string | null
  view_count: number
  // Spec 27 §5 — per-object engagement counters.
  click_count?: number
  save_count?: number
  request_info_count?: number
  apply_started_count?: number
  // Spec 27 §2.4 / §2.3 — authored CTAs + visibility scope.
  ctas?: PostCTA[] | null
  visibility?: PostVisibility | null
  created_at: string
  updated_at: string
  author_email?: string
  program_names?: string[]
}
