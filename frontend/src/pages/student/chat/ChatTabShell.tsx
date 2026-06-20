/**
 * Chat tab shell — the full-window layout for /s (the Uni advisor tab).
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §2
 *
 *   ┌──────────────┬──────────────────────────────────────────────────┐
 *   │ SessionBrowser│  DiscoverHomePage (existing Uni conversation)   │
 *   │  272px, lg+  │  unchanged, filling the rest of the viewport     │
 *   └──────────────┴──────────────────────────────────────────────────┘
 *
 * The left rail is hidden below ~860 px (lg breakpoint) — the existing
 * DiscoverHomePage owns the mobile layout (journey bar + bottom sheet).
 *
 * The conversation (DiscoverHomePage) is rendered EXACTLY as before — this
 * shell only wraps it in a flexbox with the session browser on the left.
 * No props, no state, no logic is changed inside DiscoverHomePage.
 */
import { useState } from "react";
import SessionBrowser from "./SessionBrowser";
import DiscoverHomePage from "../DiscoverHomePage";

export default function ChatTabShell() {
  // Track the active session id so the browser can highlight it.
  // Currently only used for visual feedback; wiring to the conversation
  // (managed-agent session) is a follow-on slice.
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  return (
    <div className="flex h-full w-full min-h-0 overflow-hidden">
      {/* Left rail — hidden below lg (~860 px). 272 px wide, fixed, scrollable
          internally. The conversation already handles mobile layout itself. */}
      <aside
        className="hidden lg:flex lg:w-[272px] xl:w-[272px] shrink-0 flex-col h-full"
        aria-label="Session browser"
      >
        <SessionBrowser
          activeSessionId={activeSessionId}
          onSelectSession={(id) => setActiveSessionId(id)}
          onNewSession={(id) => setActiveSessionId(id)}
        />
      </aside>

      {/* Center — the existing Uni conversation, UNCHANGED. */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        <DiscoverHomePage />
      </div>
    </div>
  );
}
