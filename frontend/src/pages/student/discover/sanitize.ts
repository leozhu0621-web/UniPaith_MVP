/**
 * Open-model safety net for the Uni thread.
 *
 * Qwen (via Together) is inconsistent about tool calling: it sometimes writes a
 * tool call as literal text (e.g. `suggest_replies(options=[...])`) instead of
 * emitting it structurally. The backend strips these from new turns, but we
 * also sanitize on render so any already-stored leak never shows in the thread.
 */
const TOOLCALL_RE =
  /`{0,3}\s*(?:suggest_replies|record_artifact|request_layer_advance)\s*\([\s\S]*?\)\s*`{0,3}/gi

/** Remove any leaked agent tool-call text from an assistant message. */
export function stripToolCalls(text: string): string {
  if (!text) return text
  return text.replace(TOOLCALL_RE, '').replace(/\n{3,}/g, '\n\n').trim()
}
