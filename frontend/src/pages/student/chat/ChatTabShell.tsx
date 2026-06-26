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
import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
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
  /** The student's first typed message from the launcher, sent as the opening
   *  turn once the conversation mounts (not just used as the session title). */
  initialMessage?: string;
}

export default function ChatTabShell() {
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);

  // Deep-link support: /s?session=<id> opens that session active. Template
  // handoffs (e.g. "Develop with Uni") also pass {originKind, originRef} via
  // router state so the session opens straight into its TemplateRunner — the
  // chat tree doesn't carry origin_ref, so state is how we know the template key.
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const deepLinkSessionId = searchParams.get("session");

  // Fetch tree so we can surface the most-recent session in the launcher and
  // resolve a deep-linked session's origin metadata.
  const { data: treeData } = useQuery({
    queryKey: ["chat-tree"],
    queryFn: getChatTree,
    retry: 1,
    staleTime: 30_000,
  });

  // Apply the ?session deep link once, after the tree loads (so we can confirm
  // the session exists and read its origin_kind). Re-applies if the param
  // changes to a different id. A guard ref keeps a manual close/select from
  // being clobbered by a re-render with the same param still in the URL.
  const appliedDeepLink = useRef<string | null>(null);
  useEffect(() => {
    if (!deepLinkSessionId || !treeData) return;
    if (appliedDeepLink.current === deepLinkSessionId) return;

    const session = treeData.folders
      .flatMap((f) => f.sessions)
      .find((s) => s.id === deepLinkSessionId);
    if (!session) return; // not ours / not yet in the tree — leave state alone

    appliedDeepLink.current = deepLinkSessionId;

    // Prefer the template metadata passed via router state (the tree omits
    // origin_ref); fall back to the session's own origin_kind for a cold link.
    const navState = location.state as
      | { originKind?: string; originRef?: string }
      | null;
    const originKind = navState?.originKind ?? session.origin_kind;
    const originRef = navState?.originRef;
    setActiveSession({ id: session.id, originKind, originRef });
  }, [deepLinkSessionId, treeData, location.state]);

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
    (id: string, originKind?: string, originRef?: string, initialMessage?: string) => {
      setActiveSession({ id, originKind: originKind ?? "manual", originRef, initialMessage });
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
            onSessionStart={(id, originKind, originRef, initialMessage) =>
              handleSessionStart(id, originKind, originRef, initialMessage)
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
              initialMessage={activeSession.initialMessage}
            />
          </div>
        )}
      </div>
    </div>
  );
}
