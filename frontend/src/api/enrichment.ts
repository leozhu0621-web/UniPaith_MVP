/**
 * AI Structure (Spec 1) — profile enrichment API client.
 * Mirrors unipaith-backend/src/unipaith/api/enrichment.py.
 */
import apiClient from "./client";

const BASE = "/students/me/enrichment";

export type AskKind = "choice" | "multi" | "scale" | "range" | "date" | "number" | "text";
export type Tier = "essential" | "high_value" | "standard";

export interface EnrichItem {
  field: string;
  type: string;
  tier: Tier;
  ask_kind: AskKind;
  action: "ask" | "confirm";
  current_value: unknown;
  confidence: number | null;
}

export interface EnrichNextResponse {
  items: EnrichItem[];
  essentials_present: boolean;
}

export async function getEnrichNext(limit = 3, section?: string): Promise<EnrichNextResponse> {
  const { data } = await apiClient.get<EnrichNextResponse>(`${BASE}/next`, {
    params: section ? { limit, section } : { limit },
  });
  return data;
}

export async function setEnrichValue(field: string, value: unknown): Promise<unknown> {
  const { data } = await apiClient.post(`${BASE}/${encodeURIComponent(field)}/value`, {
    value,
  });
  return data;
}
