/**
 * Uni chat-tab templates API client — GET /students/me/chat/templates
 *
 * Returns the active session templates with their ordered steps.
 * Used by NewSessionLauncher to render the "Start from a template" section.
 */
import apiClient from "./client";

const BASE = "/students/me/chat";

// ── Types ──────────────────────────────────────────────────────────────────

export interface TemplateStep {
  step_order: number;
  step_type: "prompt" | "action";
  prompt_key?: string;
  action_key?: string;
  label: string;
  // Prompt descriptor fields — present when step_type === "prompt"
  question?: string;
  ask_kind?: "choice" | "multi" | "scale" | "range" | "date" | "number" | "text" | "keywords" | "typeahead";
  options?: string[] | null;
  // Action label from ACTION_CATALOG — present when step_type === "action"
  action_label?: string;
}

export interface ChatTemplate {
  key: string;
  title: string;
  /** White-Paper topic folder: "profile" | "goals" | "needs" | "strategy" |
   *  "schools" | "connect" | "prepare" | "manage" */
  topic: string;
  /** "discovery" | "recommendation" | "application" */
  stage: string;
  /** Short description of what the template produces */
  outcome: string;
  /** lucide-react icon name (for future use; currently informational) */
  icon: string;
  steps: TemplateStep[];
}

// ── API ────────────────────────────────────────────────────────────────────

/** GET /students/me/chat/templates */
export async function getChatTemplates(): Promise<ChatTemplate[]> {
  const { data } = await apiClient.get<ChatTemplate[]>(`${BASE}/templates`);
  return data;
}
