/**
 * Chat tab shell — the full-window layout for /s (the Uni advisor tab).
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §2
 *
 *   ┌──────────────┬──────────────────────────────────────────────────┐
 *   │ SessionBrowser│  center view (three states):                    │
 *   │  272px, lg+  │  ── NewSessionLauncher  (no active session /    │
 *   │              │       "+ New session" clicked)                   │
 *   │              │  ── TemplateRunner  (origin_kind === "template") │
 *   │              │  ── DiscoverHomePage conversation (free session) │
 *   └──────────────┴──────────────────────────────────────────────────┘
 *
 * State:
 *   • activeSession — the session currently open in the center.
 *     null  → show NewSessionLauncher.
 *     { id, originKind: "template", originRef: <key> } → show TemplateRunner.
 *     { id, originKind: other } → show DiscoverHomePage (free conversation).
 *
 * The left rail (SessionBrowser) is hidden below ~860 px — DiscoverHomePage
 * already handles the mobile layout.  The conversation is rendered EXACTLY
 * as before; this shell only gates which view shows.
 */
import { useCallback, useState } from "react";
import SessionBrowser from "./SessionBrowser";
import NewSessionLauncher from "./NewSessionLauncher";
import TemplateRunner from "./TemplateRunner";
import DiscoverHomePage from "../DiscoverHomePage";
import { useQuery } from "@tanstack/react-query";
import { getChatTree } from "../../../api/chatSessions";

interface ActiveSession {
  id: string;
  originKind: string;
  originRef?: string;
}

export default function ChatTabShell() {
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);

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

  /** Called by NewSessionLauncher — carries origin metadata for template sessions. */
  const handleSessionStart = useCallback(
    (id: string, originKind?: string, originRef?: string) => {
      setActiveSession({ id, originKind: originKind ?? "manual", originRef });
    },
    [],
  );

  const handleSelectSession = useCallback((id: string) => {
    // Sessions opened from the browser don't carry template context (they are
    // existing sessions). Treat them as free conversations.
    setActiveSession({ id, originKind: "manual" });
  }, []);

  const handleNewSession = useCallback((id: string) => {
    setActiveSession({ id, originKind: "manual" });
  }, []);

  const handleNewSessionBlank = useCallback(() => {
    // "New session" from the browser with no id yet → show the launcher
    setActiveSession(null);
  }, []);

  // The discovery thread bound to the open session (null until its first turn).
  // Looked up from the tree so opening a session resumes its own conversation.
  const activeConversationId = (() => {
    if (!activeSession || !treeData) return null;
    for (const f of treeData.folders) {
      const s = f.sessions.find((x) => x.id === activeSession.id);
      if (s) return s.conversation_session_id ?? null;
    }
    return null;
  })();

  return (
    <div className="flex h-full w-full min-h-0 overflow-hidden">
      {/* Left rail — hidden below lg (~860 px). 272 px wide, fixed, scrollable
          internally. The conversation already handles mobile layout itself. */}
      <aside
        className="hidden lg:flex lg:w-[272px] xl:w-[272px] shrink-0 flex-col h-full"
        aria-label="Session browser"
      >
        <SessionBrowser
          activeSessionId={activeSession?.id ?? null}
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

      {/* Center view — launcher, template runner, or free conversation */}
      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {activeSession === null ? (
          /* New-session launcher */
          <NewSessionLauncher
            recentSession={recentSession}
            onSessionStart={(id, originKind, originRef) =>
              handleSessionStart(id, originKind, originRef)
            }
          />
        ) : activeSession.originKind === "template" && activeSession.originRef ? (
          /* Template runner — step-by-step guided plan */
          <TemplateRunner
            templateKey={activeSession.originRef}
            onClose={() => setActiveSession(null)}
          />
        ) : (
          /* Free Uni conversation — clean chat-tab mode (no journey rail /
             dashboard). Keyed by session id so switching sessions remounts on
             the right thread; resumes via conversationSessionId. */
          <div className="flex-1 min-w-0 overflow-y-auto">
            <DiscoverHomePage
              key={activeSession.id}
              chatTabMode
              chatSessionId={activeSession.id}
              conversationSessionId={activeConversationId}
            />
          </div>
        )}
      </div>
    </div>
  );
}
