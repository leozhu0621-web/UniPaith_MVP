/**
 * Uni chat-tab sessions API client — /students/me/chat/*
 *
 * Mirrors unipaith-backend/src/unipaith/api/chat_sessions.py.
 * The backend auto-files a new session into a folder on create; the user can
 * then move it to any folder (updateSession with folder_id) or reorder within.
 */
import apiClient from "./client";

const BASE = "/students/me/chat";

// ── Types ──────────────────────────────────────────────────────────────────

/** A topic/White-Paper stage preset folder, or a user-created custom folder. */
export interface ChatFolder {
  id: string;
  name: string;
  /** "preset" = White-Paper topic (protected); "custom" = user-created */
  kind: "preset" | "custom";
  /** Set only on preset folders: "profile" | "goals" | "needs" | "strategy" |
   *  "schools" | "connect" | "prepare" | "manage" */
  topic_key: string | null;
  /** Set only on preset folders: "discovery" | "recommendation" | "application" */
  stage: string | null;
  sort_order: number;
}

/** A named conversation thread filed inside a folder. */
export interface ChatSession {
  id: string;
  title: string;
  pinned: boolean;
  sort_order: number;
  folder_id: string;
  /** "manual" | "discover_program" | "discover_school" | "scholarship" |
   *  "event" | "peer" | "upload" */
  origin_kind: string;
  /** The topic_key of the owning folder (null if folder not returned). */
  topic_key: string | null;
  /** The discovery/conversation thread bound to this session (null until the
   *  first turn creates one). Drives session↔conversation resume. Optional so
   *  older fixtures/responses without it still type-check; the API always sends it. */
  conversation_session_id?: string | null;
}

/** A folder with its sessions — the shape returned by GET /folders. */
export interface FolderNode extends ChatFolder {
  sessions: ChatSession[];
}

/** The shape returned by GET /folders. */
export interface ChatTreeResponse {
  folders: FolderNode[];
}

// ── API functions ──────────────────────────────────────────────────────────

/** GET /students/me/chat/folders — full tree (folders + their sessions). */
export async function getChatTree(): Promise<ChatTreeResponse> {
  const { data } = await apiClient.get<ChatTreeResponse>(`${BASE}/folders`);
  return data;
}

/** POST /students/me/chat/sessions — create a new session. */
export async function createSession(params: {
  title: string;
  topic_key?: string | null;
  origin_kind?: string;
  origin_ref?: string | null;
}): Promise<ChatSession> {
  const { data } = await apiClient.post<ChatSession>(`${BASE}/sessions`, params);
  return data;
}

/** PATCH /students/me/chat/sessions/{id} — rename / pin / reorder / move a session. */
export async function updateSession(
  id: string,
  patch: {
    title?: string;
    pinned?: boolean;
    sort_order?: number;
    /** Move the session into this folder (custom or preset). */
    folder_id?: string;
    conversation_session_id?: string | null;
  },
): Promise<ChatSession> {
  const { data } = await apiClient.patch<ChatSession>(`${BASE}/sessions/${id}`, patch);
  return data;
}

/** DELETE /students/me/chat/sessions/{id} */
export async function deleteSession(id: string): Promise<void> {
  await apiClient.delete(`${BASE}/sessions/${id}`);
}

/** POST /students/me/chat/sessions/reorder — reorder sessions within a folder. */
export async function reorderSessions(
  folder_id: string,
  ordered_ids: string[],
): Promise<void> {
  await apiClient.post(`${BASE}/sessions/reorder`, { folder_id, ordered_ids });
}

/** POST /students/me/chat/folders — create a custom folder. */
export async function createFolder(name: string): Promise<ChatFolder> {
  const { data } = await apiClient.post<ChatFolder>(`${BASE}/folders`, { name });
  return data;
}

/** PATCH /students/me/chat/folders/{id} — rename or reorder a custom folder. */
export async function updateFolder(
  id: string,
  patch: { name?: string; sort_order?: number },
): Promise<ChatFolder> {
  const { data } = await apiClient.patch<ChatFolder>(`${BASE}/folders/${id}`, patch);
  return data;
}

/** DELETE /students/me/chat/folders/{id} — delete a custom folder (not preset). */
export async function deleteFolder(id: string): Promise<void> {
  await apiClient.delete(`${BASE}/folders/${id}`);
}
