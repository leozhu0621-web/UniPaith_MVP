/**
 * Spec 44 — Adaptive Intake Engine API client.
 *
 * The unified ingestion surface: one call per intake channel (§5), the
 * clarification confirm/correct loop (§6), and the read-only completeness /
 * match-ready / apply-ready gates (§4). Mirrors
 * unipaith-backend/src/unipaith/api/intake.py.
 */
import apiClient from "./client";

const BASE = "/students/me/intake";

// ── types ────────────────────────────────────────────────────────────────────
export interface IngestResult {
  signal_name: string;
  status: "created" | "updated" | "reconciled_kept";
  value: unknown;
  value_normalized?: unknown;
  confidence: number;
  source: string;
  record_version: number;
  valid?: boolean;
  clarification_id?: string | null;
}

export interface CompletenessSignal {
  signal_name: string;
  label: string;
  present: boolean;
  confidence: number | null;
  source: string | null;
  required_for_match: boolean;
}

export interface CompletenessCategory {
  category: string;
  present: number;
  total: number;
  pct: number;
  signals: CompletenessSignal[];
}

export interface Completeness {
  overall_profile_completeness_pct: number;
  present_signals: number;
  total_signals: number;
  categories: CompletenessCategory[];
}

export interface MatchReadyMissing {
  signal_name: string;
  label: string;
  category: string;
  kind: "required_field" | "geography" | "priorities";
  detail?: string;
}

export interface MatchReady {
  match_ready: boolean;
  completeness_pct: number;
  pct_floor: number;
  missing: MatchReadyMissing[];
  missing_count: number;
  required_total: number;
}

export interface ApplyReadyRequirement {
  key: string;
  label: string;
  satisfied: boolean;
  detail: string;
  advisory?: boolean;
}

export interface ApplyReady {
  program_id: string;
  program_name: string;
  ready_to_submit: boolean;
  requirements: ApplyReadyRequirement[];
}

export interface Clarification {
  id: string;
  signal_name: string;
  label: string;
  question: string;
  raw_value: unknown;
  suggested_value: unknown;
  confidence: number;
  created_at: string | null;
}

// ── §5 ingestion ─────────────────────────────────────────────────────────────
export const formSave = (signalName: string, value: unknown): Promise<IngestResult> =>
  apiClient.post(`${BASE}/form-save`, { signal_name: signalName, value }).then((r) => r.data);

export const ingestMessage = (sessionId: string, content: string): Promise<unknown> =>
  apiClient.post(`${BASE}/messages`, { session_id: sessionId, content }).then((r) => r.data);

export const ingestExternalLink = (url: string, kind: string): Promise<IngestResult> =>
  apiClient.post(`${BASE}/external-link`, { url, kind }).then((r) => r.data);

// ── §6 clarifications ────────────────────────────────────────────────────────
export const listClarifications = (): Promise<{ clarifications: Clarification[] }> =>
  apiClient.get(`${BASE}/clarifications`).then((r) => r.data);

export const resolveClarification = (
  id: string,
  action: "confirm" | "correct",
  value?: unknown,
): Promise<unknown> =>
  apiClient.post(`${BASE}/clarifications/${id}/confirm`, { action, value }).then((r) => r.data);

// ── §4 gates ─────────────────────────────────────────────────────────────────
export const getCompleteness = (): Promise<Completeness> =>
  apiClient.get(`${BASE}/completeness`).then((r) => r.data);

export const getMatchReady = (): Promise<MatchReady> =>
  apiClient.get(`${BASE}/match-ready`).then((r) => r.data);

export const getApplyReady = (programId: string): Promise<ApplyReady> =>
  apiClient.get(`${BASE}/apply-ready/${programId}`).then((r) => r.data);
