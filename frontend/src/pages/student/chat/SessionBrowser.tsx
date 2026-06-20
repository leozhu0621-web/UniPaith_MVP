/**
 * Intelligent session browser — left rail of the Uni chat tab.
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §3
 * Visual reference: .superpowers/brainstorm/…/content/chat-tab-v12.html
 *
 * Structure:
 *   ─ Search box
 *   ─ + New session  /  New folder
 *   ─ Pinned (sessions with pinned=true)
 *   ─ Your folders (custom, kind="custom")
 *   ─ Discovery       (preset, stage="discovery")
 *   ─ Recommendation  (preset, stage="recommendation")
 *   ─ Application Strategy & Support  (preset, stage="application")
 *
 * Rules:
 *   • Preset folder ⋯ menu:  "New session here" · "Collapse" — NO delete/rename.
 *   • Custom folder ⋯ menu:  "Rename" · "New session here" · "Delete folder".
 *   • Session ⋯ menu:        "Rename" · "Pin / Unpin" · "Delete".
 *   • Session cannot be moved to a different folder (auto-categorisation owns that).
 */
import { useRef, useState } from "react";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Search,
  Plus,
  FolderPlus,
  ChevronRight,
  Pin,
  MoreHorizontal,
  GripVertical,
  Trash2,
  Pencil,
  CheckCheck,
} from "lucide-react";
import type { FolderNode, ChatSession } from "../../../api/chatSessions";
import {
  getChatTree,
  createSession,
  updateSession,
  deleteSession,
  createFolder,
  updateFolder,
  deleteFolder,
} from "../../../api/chatSessions";

// ── Query key ──────────────────────────────────────────────────────────────
const CHAT_TREE_KEY = ["chat-tree"] as const;

// ── Stage labels ──────────────────────────────────────────────────────────
const STAGE_LABELS: Record<string, string> = {
  discovery: "Discovery",
  recommendation: "Recommendation",
  application: "Application Strategy & Support",
};

// ── Props ──────────────────────────────────────────────────────────────────
interface Props {
  /** ID of the currently active session (highlighted). */
  activeSessionId?: string | null;
  /** Called when the user picks a session. */
  onSelectSession?: (sessionId: string) => void;
  /** Called when a brand-new session is created (so the parent can wire it). */
  /** Called when the user starts a new session. With a sessionId, open it.
   *  With no id (the top "+ New session"), the shell shows the launcher so the
   *  session is named + auto-filed from real content (no blank "New session"). */
  onNewSession?: (sessionId?: string) => void;
}

// ── Inline-rename helper ───────────────────────────────────────────────────
function InlineInput({
  initial,
  onCommit,
  onCancel,
}: {
  initial: string;
  onCommit: (v: string) => void;
  onCancel: () => void;
}) {
  const [val, setVal] = useState(initial);
  return (
    <input
      autoFocus
      value={val}
      onChange={(e) => setVal(e.target.value)}
      onBlur={() => onCommit(val.trim() || initial)}
      onKeyDown={(e) => {
        if (e.key === "Enter") onCommit(val.trim() || initial);
        if (e.key === "Escape") onCancel();
        e.stopPropagation();
      }}
      onClick={(e) => e.stopPropagation()}
      className="flex-1 min-w-0 bg-transparent border-b border-secondary text-foreground text-[13px] outline-none"
    />
  );
}

// ── Context-menu popover ───────────────────────────────────────────────────
interface MenuItem {
  label: string;
  icon?: React.ReactNode;
  danger?: boolean;
  onClick: () => void;
}

function ContextMenu({
  items,
  onClose,
}: {
  items: MenuItem[];
  onClose: () => void;
}) {
  // Close on outside click
  const menuRef = useRef<HTMLDivElement>(null);

  return (
    <>
      {/* backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={(e) => { e.stopPropagation(); onClose(); }}
      />
      <div
        ref={menuRef}
        role="menu"
        className="absolute right-0 top-full z-50 mt-1 min-w-[170px] rounded-[10px] border border-border bg-card shadow-[0_6px_16px_-4px_rgba(10,20,40,.14),0_2px_4px_rgba(10,20,40,.07)] py-1 animate-in fade-in zoom-in-95 duration-100"
        onClick={(e) => e.stopPropagation()}
      >
        {items.map((item, i) =>
          item.label === "__divider__" ? (
            <hr key={i} className="my-1 border-border" />
          ) : (
            <button
              key={i}
              role="menuitem"
              onClick={() => { item.onClick(); onClose(); }}
              className={`flex w-full items-center gap-2.5 px-3 py-2 text-[13px] font-semibold text-left rounded-lg mx-0.5 transition-colors hover:bg-muted ${
                item.danger ? "text-destructive" : "text-foreground"
              }`}
            >
              {item.icon && <span className="shrink-0 text-muted-foreground">{item.icon}</span>}
              {item.label}
            </button>
          ),
        )}
      </div>
    </>
  );
}

// ── Session row ────────────────────────────────────────────────────────────
function SessionRow({
  session,
  isActive,
  onSelect,
  onRename,
  onPin,
  onDelete,
}: {
  session: ChatSession;
  isActive: boolean;
  onSelect: () => void;
  onRename: (title: string) => void;
  onPin: () => void;
  onDelete: () => void;
}) {
  const [menu, setMenu] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const menuBtnRef = useRef<HTMLButtonElement>(null);

  const menuItems: MenuItem[] = [
    {
      label: "Rename",
      icon: <Pencil size={13} />,
      onClick: () => setRenaming(true),
    },
    {
      label: session.pinned ? "Unpin" : "Pin",
      icon: <Pin size={13} />,
      onClick: onPin,
    },
    { label: "__divider__", onClick: () => {} },
    {
      label: "Delete",
      icon: <Trash2 size={13} />,
      danger: true,
      onClick: onDelete,
    },
  ];

  return (
    <div
      draggable
      role="option"
      aria-selected={isActive}
      onClick={() => !renaming && onSelect()}
      className={`group relative flex items-center gap-2 pl-[21px] pr-2 py-[7px] my-0.5 ml-3.5 border-l-2 rounded-r-lg cursor-pointer text-[13px] transition-colors select-none ${
        isActive
          ? "border-l-primary bg-[hsl(var(--primary)/0.12)] text-foreground font-semibold"
          : "border-l-border hover:bg-muted hover:text-foreground text-muted-foreground"
      }`}
    >
      {/* drag grip — fades in on hover */}
      <span className="absolute left-1.5 top-0 bottom-0 flex items-center opacity-0 group-hover:opacity-50 transition-opacity text-muted-foreground">
        <GripVertical size={13} />
      </span>

      {/* pinned indicator */}
      {session.pinned && (
        <Pin size={11} className="shrink-0 text-primary" aria-label="Pinned" />
      )}

      {renaming ? (
        <InlineInput
          initial={session.title}
          onCommit={(v) => { setRenaming(false); if (v !== session.title) onRename(v); }}
          onCancel={() => setRenaming(false)}
        />
      ) : (
        <span className="flex-1 truncate">{session.title}</span>
      )}

      {/* context-spawned badge */}
      {session.origin_kind !== "manual" && (
        <span className="shrink-0 text-[9px] font-bold uppercase tracking-wide text-secondary bg-secondary/10 rounded-full px-1.5 py-0.5">
          {session.origin_kind === "discover_program" || session.origin_kind === "discover_school"
            ? "Discover"
            : session.origin_kind}
        </span>
      )}

      {/* ⋯ menu trigger */}
      <div className="relative shrink-0">
        <button
          ref={menuBtnRef}
          aria-label="Session options"
          onClick={(e) => { e.stopPropagation(); setMenu((v) => !v); }}
          className="opacity-0 group-hover:opacity-70 hover:!opacity-100 p-0.5 rounded text-muted-foreground transition-opacity"
        >
          <MoreHorizontal size={14} />
        </button>
        {menu && (
          <ContextMenu
            items={menuItems}
            onClose={() => setMenu(false)}
          />
        )}
      </div>
    </div>
  );
}

// ── Folder block ───────────────────────────────────────────────────────────
function FolderBlock({
  node,
  activeSessionId,
  onSelectSession,
  onRenameSession,
  onPinSession,
  onDeleteSession,
  onNewSessionHere,
  onRenameFolder,
  onDeleteFolder,
}: {
  node: FolderNode;
  activeSessionId?: string | null;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, title: string) => void;
  onPinSession: (id: string, pinned: boolean) => void;
  onDeleteSession: (id: string) => void;
  onNewSessionHere: (folderId: string, topicKey: string | null) => void;
  onRenameFolder: (id: string, name: string) => void;
  onDeleteFolder: (id: string) => void;
}) {
  const [open, setOpen] = useState(node.sessions.length > 0);
  const [menu, setMenu] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const menuBtnRef = useRef<HTMLButtonElement>(null);
  const isPreset = node.kind === "preset";

  const presetMenuItems: MenuItem[] = [
    {
      label: "New session here",
      icon: <Plus size={13} />,
      onClick: () => onNewSessionHere(node.id, node.topic_key),
    },
    {
      label: open ? "Collapse" : "Expand",
      icon: <ChevronRight size={13} />,
      onClick: () => setOpen((v) => !v),
    },
  ];

  const customMenuItems: MenuItem[] = [
    {
      label: "Rename",
      icon: <Pencil size={13} />,
      onClick: () => setRenaming(true),
    },
    {
      label: "New session here",
      icon: <Plus size={13} />,
      onClick: () => onNewSessionHere(node.id, node.topic_key),
    },
    { label: "__divider__", onClick: () => {} },
    {
      label: "Delete folder",
      icon: <Trash2 size={13} />,
      danger: true,
      onClick: () => onDeleteFolder(node.id),
    },
  ];

  return (
    <div className="mb-0.5">
      {/* folder header */}
      <div
        className="group relative flex items-center gap-2 px-2.5 py-2 rounded-[10px] cursor-pointer hover:bg-muted transition-colors"
        onClick={(e) => {
          if ((e.target as HTMLElement).closest("button, input")) return;
          setOpen((v) => !v);
        }}
        role="button"
        aria-expanded={open}
      >
        {/* grip handle (fades in on hover for drag-reorder of folder within group) */}
        <span className="absolute left-1 top-0 bottom-0 flex items-center opacity-0 group-hover:opacity-40 transition-opacity text-muted-foreground">
          <GripVertical size={13} />
        </span>

        {/* expand chevron */}
        <ChevronRight
          size={12}
          className={`shrink-0 text-muted-foreground transition-transform duration-[280ms] ease-out ${open ? "rotate-90" : ""}`}
        />

        {renaming ? (
          <InlineInput
            initial={node.name}
            onCommit={(v) => { setRenaming(false); if (v !== node.name) onRenameFolder(node.id, v); }}
            onCancel={() => setRenaming(false)}
          />
        ) : (
          <span className="flex-1 truncate text-[13.5px] font-bold text-foreground">
            {node.name}
          </span>
        )}

        {/* session count badge */}
        <span
          className={`text-[11px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 ${
            node.sessions.length === 0
              ? "text-border"
              : "text-muted-foreground bg-muted"
          }`}
        >
          {node.sessions.length}
        </span>

        {/* ⋯ menu */}
        <div className="relative shrink-0">
          <button
            ref={menuBtnRef}
            aria-label={`${node.name} folder options`}
            onClick={(e) => { e.stopPropagation(); setMenu((v) => !v); }}
            className="opacity-0 group-hover:opacity-60 hover:!opacity-100 p-0.5 rounded text-muted-foreground transition-opacity"
          >
            <MoreHorizontal size={14} />
          </button>
          {menu && (
            <ContextMenu
              items={isPreset ? presetMenuItems : customMenuItems}
              onClose={() => setMenu(false)}
            />
          )}
        </div>
      </div>

      {/* collapsible sessions list */}
      <div
        className="overflow-hidden transition-[grid-template-rows] duration-300 ease-out"
        style={{
          display: "grid",
          gridTemplateRows: open ? "1fr" : "0fr",
        }}
      >
        <div className="min-h-0 overflow-hidden">
          {node.sessions.map((s) => (
            <SessionRow
              key={s.id}
              session={s}
              isActive={activeSessionId === s.id}
              onSelect={() => onSelectSession(s.id)}
              onRename={(title) => onRenameSession(s.id, title)}
              onPin={() => onPinSession(s.id, !s.pinned)}
              onDelete={() => onDeleteSession(s.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export default function SessionBrowser({
  activeSessionId,
  onSelectSession,
  onNewSession,
}: Props) {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [newFolderMode, setNewFolderMode] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: CHAT_TREE_KEY,
    queryFn: getChatTree,
    retry: 1,
  });

  // ── mutations ────────────────────────────────────────────────────────────
  const invalidate = () => qc.invalidateQueries({ queryKey: CHAT_TREE_KEY });

  const createSessionMut = useMutation({
    mutationFn: createSession,
    onSuccess: (s) => { invalidate(); onNewSession?.(s.id); },
  });

  const updateSessionMut = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Parameters<typeof updateSession>[1] }) =>
      updateSession(id, patch),
    onSuccess: invalidate,
  });

  const deleteSessionMut = useMutation({
    mutationFn: deleteSession,
    onSuccess: invalidate,
  });

  const createFolderMut = useMutation({
    mutationFn: createFolder,
    onSuccess: invalidate,
  });

  const updateFolderMut = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Parameters<typeof updateFolder>[1] }) =>
      updateFolder(id, patch),
    onSuccess: invalidate,
  });

  const deleteFolderMut = useMutation({
    mutationFn: deleteFolder,
    onSuccess: invalidate,
  });

  // ── derived data ─────────────────────────────────────────────────────────
  const folders = data?.folders ?? [];

  // Filter by search (sessions whose title matches; always show folder headers)
  const q = search.trim().toLowerCase();
  const filtered: FolderNode[] = q
    ? folders.map((f) => ({
        ...f,
        sessions: f.sessions.filter((s) =>
          s.title.toLowerCase().includes(q),
        ),
      })).filter((f) => f.sessions.length > 0)
    : folders;

  // Pinned sessions (across all folders)
  const pinned = folders.flatMap((f) => f.sessions).filter((s) => s.pinned);

  // Partition folders by kind + stage
  const customFolders = filtered.filter((f) => f.kind === "custom");
  const discovery = filtered.filter(
    (f) => f.kind === "preset" && f.stage === "discovery",
  );
  const recommendation = filtered.filter(
    (f) => f.kind === "preset" && f.stage === "recommendation",
  );
  const application = filtered.filter(
    (f) => f.kind === "preset" && f.stage === "application",
  );

  // ── actions ───────────────────────────────────────────────────────────────
  function handleNewSession(topicKey?: string | null) {
    createSessionMut.mutate({
      title: "New session",
      topic_key: topicKey ?? undefined,
      origin_kind: "manual",
    });
  }

  function handleNewFolder() {
    const name = newFolderName.trim();
    if (!name) return;
    createFolderMut.mutate(name);
    setNewFolderName("");
    setNewFolderMode(false);
  }

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div
      className="flex flex-col h-full bg-card border-r border-border overflow-hidden"
      aria-label="Session browser"
    >
      {/* scrollable content */}
      <div className="flex-1 overflow-y-auto px-[11px] py-[14px] space-y-0">
        {/* Search */}
        <div className="flex items-center gap-2 px-3 py-[9px] mb-[9px] border border-border rounded-[10px] bg-background text-muted-foreground text-[13px]">
          <Search size={14} className="shrink-0" />
          <input
            type="search"
            placeholder="Search sessions"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground text-[13px]"
            aria-label="Search sessions"
          />
        </div>

        {/* Buttons row */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => onNewSession?.()}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-[10px] bg-secondary text-secondary-foreground text-[13px] font-bold hover:bg-secondary/90 transition-colors"
          >
            <Plus size={14} strokeWidth={2.5} />
            New session
          </button>
          <button
            onClick={() => setNewFolderMode((v) => !v)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-[10px] border border-border bg-transparent text-foreground text-[13px] font-bold hover:border-secondary hover:text-secondary transition-colors"
          >
            <FolderPlus size={14} />
            New folder
          </button>
        </div>

        {/* New folder inline input */}
        {newFolderMode && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 rounded-[10px] border border-secondary bg-secondary/5">
            <input
              autoFocus
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleNewFolder();
                if (e.key === "Escape") { setNewFolderMode(false); setNewFolderName(""); }
              }}
              placeholder="Folder name"
              className="flex-1 bg-transparent border-none outline-none text-[13px] text-foreground placeholder:text-muted-foreground"
            />
            <button
              onClick={handleNewFolder}
              disabled={!newFolderName.trim()}
              className="text-secondary hover:text-secondary/80 disabled:opacity-40"
              aria-label="Create folder"
            >
              <CheckCheck size={15} />
            </button>
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && (
          <div className="space-y-2 animate-pulse px-1">
            {[80, 60, 70, 55].map((w, i) => (
              <div
                key={i}
                className="h-8 rounded-lg bg-muted"
                style={{ width: `${w}%` }}
              />
            ))}
          </div>
        )}

        {/* Pinned */}
        {!isLoading && !q && pinned.length > 0 && (
          <section aria-label="Pinned sessions" className="mb-3">
            <p className="text-[11px] font-bold tracking-[0.13em] uppercase text-border mb-1.5 ml-2">
              Pinned
            </p>
            {pinned.map((s) => (
              <SessionRow
                key={s.id}
                session={s}
                isActive={activeSessionId === s.id}
                onSelect={() => onSelectSession?.(s.id)}
                onRename={(title) =>
                  updateSessionMut.mutate({ id: s.id, patch: { title } })
                }
                onPin={() =>
                  updateSessionMut.mutate({ id: s.id, patch: { pinned: false } })
                }
                onDelete={() => deleteSessionMut.mutate(s.id)}
              />
            ))}
          </section>
        )}

        {/* Custom folders */}
        {!isLoading && customFolders.length > 0 && (
          <section aria-label="Your folders" className="mb-3">
            <p className="text-[11px] font-bold tracking-[0.13em] uppercase text-border mb-1.5 ml-2">
              Your folders
            </p>
            {customFolders.map((f) => (
              <FolderBlock
                key={f.id}
                node={f}
                activeSessionId={activeSessionId}
                onSelectSession={(id) => onSelectSession?.(id)}
                onRenameSession={(id, title) =>
                  updateSessionMut.mutate({ id, patch: { title } })
                }
                onPinSession={(id, pinned) =>
                  updateSessionMut.mutate({ id, patch: { pinned } })
                }
                onDeleteSession={(id) => deleteSessionMut.mutate(id)}
                onNewSessionHere={(_fid, topicKey) => handleNewSession(topicKey)}
                onRenameFolder={(id, name) =>
                  updateFolderMut.mutate({ id, patch: { name } })
                }
                onDeleteFolder={(id) => deleteFolderMut.mutate(id)}
              />
            ))}
          </section>
        )}

        {/* Preset folders grouped by stage */}
        {!isLoading &&
          (
            [
              { stage: "discovery", nodes: discovery },
              { stage: "recommendation", nodes: recommendation },
              { stage: "application", nodes: application },
            ] as const
          ).map(({ stage, nodes }) =>
            nodes.length === 0 ? null : (
              <section key={stage} aria-label={STAGE_LABELS[stage]} className="mb-3">
                <p className="text-[11px] font-bold tracking-[0.13em] uppercase text-border mb-1.5 ml-2">
                  {STAGE_LABELS[stage]}
                </p>
                {nodes.map((f) => (
                  <FolderBlock
                    key={f.id}
                    node={f}
                    activeSessionId={activeSessionId}
                    onSelectSession={(id) => onSelectSession?.(id)}
                    onRenameSession={(id, title) =>
                      updateSessionMut.mutate({ id, patch: { title } })
                    }
                    onPinSession={(id, pinned) =>
                      updateSessionMut.mutate({ id, patch: { pinned } })
                    }
                    onDeleteSession={(id) => deleteSessionMut.mutate(id)}
                    onNewSessionHere={(_fid, topicKey) => handleNewSession(topicKey)}
                    onRenameFolder={() => {}} // preset: no rename
                    onDeleteFolder={() => {}} // preset: no delete
                  />
                ))}
              </section>
            ),
          )}

        {/* Empty state when search returns nothing */}
        {!isLoading && q && filtered.length === 0 && (
          <p className="text-center text-[13px] text-muted-foreground py-8">
            No sessions match &ldquo;{search}&rdquo;
          </p>
        )}
      </div>
    </div>
  );
}
