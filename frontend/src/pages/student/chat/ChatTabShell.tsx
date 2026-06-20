/**
 * Chat tab shell — the full-window layout for /s (the Uni advisor tab).
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §2
 *
 *   ┌──────────────┬──────────────────────────────────────────────────┐
 *   │ SessionBrowser│  center view (two states):                      │
 *   │  272px, lg+  │  ── NewSessionLauncher  (no active session /    │
 *   │              │       "+ New session" clicked)                   │
 *   │              │  ── DiscoverHomePage conversation (active sess.) │
 *   └──────────────┴──────────────────────────────────────────────────┘
 *
 * State:
 *   • activeSessionId — the session currently open in the center.
 *     null  → show NewSessionLauncher.
 *     non-null → show DiscoverHomePage (existing Uni conversation).
 *
 * The left rail (SessionBrowser) is hidden below ~860 px — DiscoverHomePage
 * already handles the mobile layout.  The conversation is rendered EXACTLY
 * as before; this shell only gates which view shows.
 */
import { useCallback, useState } from "react";
import SessionBrowser from "./SessionBrowser";
import NewSessionLauncher from "./NewSessionLauncher";
import DiscoverHomePage from "../DiscoverHomePage";
import { useQuery } from "@tanstack/react-query";
import { getChatTree } from "../../../api/chatSessions";

export default function ChatTabShell() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Fetch tree so we can surface the most-recent session in the launcher.
  const { data: treeData } = useQuery({
    queryKey: ["chat-tree"],
    queryFn: getChatTree,
    retry: 1,
    staleTime: 30_000,
  });

  // Most-recent session (first session across any folder, by sort_order asc).
  const recentSession = (() => {
    if (!treeData) return null;
    const allSessions = treeData.folders.flatMap((f) =>
      f.sessions.map((s) => ({
        id: s.id,
        title: s.title,
        stage: f.stage,
      })),
    );
    if (allSessions.length === 0) return null;
    return allSessions[0]; // folders/sessions returned in sort_order order
  })();

  const handleSessionStart = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const handleNewSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const handleNewSessionBlank = useCallback(() => {
    // "New session" from the browser with no id yet → show the launcher
    setActiveSessionId(null);
  }, []);

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
          onSelectSession={handleSelectSession}
          onNewSession={(id) => {
            // When the browser creates a session and returns an id, open it.
            // When the user clicks "+ New session" from the top button, the
            // browser calls onNewSession after creating a session; we switch
            // to the conversation immediately.
            if (id) {
              handleNewSession(id);
            } else {
              handleNewSessionBlank();
            }
          }}
        />
      </aside>

      {/* Center view — launcher or conversation */}
      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {activeSessionId === null ? (
          /* New-session launcher */
          <NewSessionLauncher
            recentSession={recentSession}
            onSessionStart={handleSessionStart}
          />
        ) : (
          /* Existing Uni conversation — unchanged */
          <div className="flex-1 min-w-0 overflow-y-auto">
            <DiscoverHomePage />
          </div>
        )}
      </div>
    </div>
  );
}
