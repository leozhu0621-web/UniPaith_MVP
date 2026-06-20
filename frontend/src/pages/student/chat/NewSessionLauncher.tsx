/**
 * NewSessionLauncher — the center "new session" screen on the Uni chat tab.
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §4
 * Visual ref: .superpowers/brainstorm/13637-1781904184/content/chat-tab-v12.html
 *
 * Layout (ChatGPT-style empty state, organized by product taxonomy):
 *   ─ Hero: orb + "Where would you like to start?"
 *   ─ Input bar (free text) + + upload affordance + cobalt send
 *   ─ Continue    — most-recent session (if any; prop-injected)
 *   ─ For you     — 4 action cards (representative, non-personalized this slice)
 *   ─ Academic    — 2 campus photo cards + 2 event/program cards (representative)
 *   ─ Financial   — 1 scholarship card + 3 action cards (representative)
 *   ─ International — 2 guide cards + 2 country cards (representative)
 *   ─ Peers       — 3 peer avatar cards + 1 "Find more" card (representative)
 *   ─ Start from a template — live chips from getChatTemplates(), grouped by stage
 *
 * NOTE: "Academic", "Financial", "International", "Peers" cards are static/
 * representative this slice. Real data endpoints exist (universities, scholarships,
 * events, peers) but wiring them up is a follow-on slice after the launcher ships.
 *
 * Picking a card/chip OR submitting the input calls createSession() and signals
 * the parent shell via onSessionStart(sessionId).
 *
 * The upload "+" opens a stub menu (Upload a file / Add a photo / From My Space).
 * The full ingest pipeline is wired in the conversation (existing material-ingest
 * pipeline); this slice only provides the affordance.
 */

import { useRef, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, ArrowUp, BookOpen, List, Scale, Compass, Flag, Heart, Calendar, Users } from "lucide-react";
import { getChatTemplates, type ChatTemplate } from "../../../api/chatTemplates";
import { createSession, type ChatSession } from "../../../api/chatSessions";

// ── Props ──────────────────────────────────────────────────────────────────

interface Props {
  /** The most-recent active session to show in the "Continue" card.
   *  Null when there are no prior sessions. */
  recentSession?: { id: string; title: string; stage?: string | null } | null;
  /** Called when a session is started (created or re-opened).
   *  originKind and originRef are forwarded for template sessions so the shell
   *  can route to TemplateRunner. */
  onSessionStart: (sessionId: string, originKind?: string, originRef?: string) => void;
}

// ── Stage labels for template grouping ────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  discovery: "Discovery",
  recommendation: "Recommendation",
  application: "Application Strategy & Support",
};

// ── Orb ─────────────────────────────────────────────────────────────────

function UniOrb({ size = 48 }: { size?: number }) {
  return (
    <div
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        flexShrink: 0,
        background: "radial-gradient(circle at 38% 34%, hsl(var(--primary)), hsl(var(--secondary)) 80%)",
        boxShadow: "0 0 18px 1px hsl(var(--primary) / 0.35)",
      }}
    />
  );
}

// ── Upload stub menu ───────────────────────────────────────────────────────

const UPLOAD_ITEMS = ["Upload a file", "Add a photo", "From My Space"] as const;

function UploadMenu({ anchor, onClose }: { anchor: DOMRect; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div
        role="menu"
        aria-label="Upload options"
        className="fixed z-50 min-w-[180px] rounded-[10px] border border-border bg-card shadow-[0_6px_16px_-4px_rgba(10,20,40,.14),0_2px_4px_rgba(10,20,40,.07)] py-1 animate-in fade-in zoom-in-95 duration-100"
        style={{
          left: Math.max(8, anchor.left),
          bottom: window.innerHeight - anchor.top + 6,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {UPLOAD_ITEMS.map((item) => (
          <button
            key={item}
            role="menuitem"
            onClick={onClose}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-[13px] font-semibold text-left text-foreground hover:bg-muted transition-colors"
          >
            {item}
          </button>
        ))}
      </div>
    </>
  );
}

// ── Card helpers ───────────────────────────────────────────────────────────

function EyebrowLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-bold tracking-[0.2em] uppercase text-secondary mb-3">
      {children}
    </p>
  );
}

/** Icon action card — icon + bold title. */
function ActionCard({
  icon,
  title,
  goldAccent,
  onClick,
}: {
  icon: React.ReactNode;
  title: string;
  goldAccent?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col gap-3 rounded-[14px] border border-border bg-card p-4 text-left shadow-[0_1px_2px_rgba(10,20,40,.06),0_1px_1px_rgba(10,20,40,.04)] transition-all hover:-translate-y-[3px] hover:shadow-[0_6px_16px_-4px_rgba(10,20,40,.12),0_2px_4px_rgba(10,20,40,.06)] hover:border-border/80 min-h-[116px]"
    >
      <div
        className={`w-9 h-9 rounded-[10px] flex items-center justify-center ${
          goldAccent
            ? "bg-[hsl(var(--primary)/0.15)] text-[hsl(var(--primary)/0.8)]"
            : "bg-muted text-secondary"
        }`}
      >
        {icon}
      </div>
      <span className="text-[14.5px] font-bold leading-snug text-foreground">{title}</span>
    </button>
  );
}

/** Visual card — campus photo header fading into card bg. */
function VisualCard({
  title,
  subtitle,
  tag,
  imgUrl,
  imgCredit,
  onClick,
}: {
  title: string;
  subtitle?: string;
  tag?: string;
  imgUrl: string;
  imgCredit?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col rounded-[14px] border border-border bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] transition-all hover:-translate-y-[3px] hover:shadow-[0_6px_16px_-4px_rgba(10,20,40,.12)] hover:border-border/80 overflow-hidden text-left"
    >
      <div className="relative h-[94px] bg-muted">
        <img
          src={imgUrl}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />
        {/* fade to card bg */}
        <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-card to-transparent" />
        {imgCredit && (
          <span className="absolute top-1.5 right-2 text-[9px] text-white/70 drop-shadow font-semibold">
            {imgCredit}
          </span>
        )}
      </div>
      <div className="px-3 pt-2.5 pb-3 flex flex-col gap-1">
        <p className="text-[14px] font-bold leading-snug text-foreground">{title}</p>
        {subtitle && <p className="text-[12px] text-muted-foreground">{subtitle}</p>}
        {tag && (
          <span className="inline-block text-[10.5px] font-bold px-2 py-[3px] rounded-full bg-secondary/10 text-secondary mt-1">
            {tag}
          </span>
        )}
      </div>
    </button>
  );
}

/** Peer avatar card — round photo + name + program. */
function PeerCard({
  name,
  program,
  imgUrl,
  onClick,
}: {
  name: string;
  program: string;
  imgUrl: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col items-center rounded-[14px] border border-border bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] transition-all hover:-translate-y-[3px] hover:shadow-[0_6px_16px_-4px_rgba(10,20,40,.12)] hover:border-border/80 py-4 px-3 text-center"
    >
      <img
        src={imgUrl}
        alt={name}
        className="w-14 h-14 rounded-full object-cover mb-2.5"
        loading="lazy"
      />
      <p className="text-[14px] font-bold text-foreground leading-snug">{name}</p>
      <p className="text-[12px] text-muted-foreground mt-0.5">{program}</p>
    </button>
  );
}

/** Scholarship / financial highlight card. */
function ScholarshipCard({
  name,
  amount,
  note,
  onClick,
}: {
  name: string;
  amount: string;
  note: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col gap-1.5 rounded-[14px] border border-border bg-card p-4 text-left shadow-[0_1px_2px_rgba(10,20,40,.06)] transition-all hover:-translate-y-[3px] hover:shadow-[0_6px_16px_-4px_rgba(10,20,40,.12)] hover:border-border/80 min-h-[116px]"
    >
      <div className="w-9 h-9 rounded-[10px] flex items-center justify-center bg-[hsl(var(--primary)/0.12)] text-[hsl(var(--primary)/0.8)]">
        <BookOpen size={18} strokeWidth={1.6} />
      </div>
      <p className="text-[21px] font-bold text-foreground leading-none mt-1">{amount}</p>
      <p className="text-[13.5px] font-bold text-foreground leading-snug">{name}</p>
      <p className="text-[12px] text-muted-foreground">{note}</p>
    </button>
  );
}

/** Continue card — re-opens the most-recent session. */
function ContinueCard({
  title,
  stage,
  onClick,
}: {
  title: string;
  stage?: string | null;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 rounded-[14px] border border-border bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] px-4 py-3.5 w-full max-w-[420px] text-left transition-colors hover:shadow-[0_6px_16px_-4px_rgba(10,20,40,.12)] hover:border-border/80"
    >
      {/* mini orb */}
      <div
        aria-hidden="true"
        className="w-9 h-9 rounded-[10px] shrink-0"
        style={{
          background: "radial-gradient(circle at 38% 34%, hsl(var(--primary)), hsl(var(--secondary)) 80%)",
        }}
      />
      <div className="flex flex-col min-w-0">
        <p className="text-[14px] font-bold text-foreground truncate">{title}</p>
        {stage && (
          <p className="text-[12px] text-muted-foreground">
            {STAGE_LABELS[stage] ?? stage}
          </p>
        )}
      </div>
    </button>
  );
}

// ── Template chips section ─────────────────────────────────────────────────

function TemplateIcon({ icon }: { icon: string }) {
  const icons: Record<string, React.ReactNode> = {
    pen: <BookOpen size={14} strokeWidth={1.6} />,
    flag: <Flag size={14} strokeWidth={1.6} />,
    heart: <Heart size={14} strokeWidth={1.6} />,
    compass: <Compass size={14} strokeWidth={1.6} />,
    list: <List size={14} strokeWidth={1.6} />,
    scale: <Scale size={14} strokeWidth={1.6} />,
    calendar: <Calendar size={14} strokeWidth={1.6} />,
    book: <BookOpen size={14} strokeWidth={1.6} />,
  };
  return <>{icons[icon] ?? <BookOpen size={14} strokeWidth={1.6} />}</>;
}

function TemplatesSection({
  templates,
  onPick,
}: {
  templates: ChatTemplate[];
  onPick: (template: ChatTemplate) => void;
}) {
  // Group by stage, preserving the canonical order
  const order = ["discovery", "recommendation", "application"];
  const byStage: Record<string, ChatTemplate[]> = {};
  for (const t of templates) {
    (byStage[t.stage] ??= []).push(t);
  }

  return (
    <div className="space-y-4">
      {order.map((stage) => {
        const group = byStage[stage];
        if (!group || group.length === 0) return null;
        return (
          <div key={stage}>
            <p className="text-[11px] font-bold tracking-[0.13em] uppercase text-muted-foreground mb-2">
              {STAGE_LABELS[stage] ?? stage}
            </p>
            <div className="flex flex-wrap gap-2">
              {group.map((tmpl) => (
                <button
                  key={tmpl.key}
                  onClick={() => onPick(tmpl)}
                  title={tmpl.outcome}
                  className="flex items-center gap-1.5 border border-border bg-card rounded-full px-3.5 py-2 text-[13px] font-bold text-foreground transition-colors hover:border-secondary hover:text-secondary"
                >
                  <span className="text-muted-foreground">
                    <TemplateIcon icon={tmpl.icon} />
                  </span>
                  {tmpl.title}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Static card data (representative — real data wired in a later slice) ──

// Academic — campus/program/event cards
// Images: Unsplash open license, credited inline as required.
const ACADEMIC_CARDS = [
  {
    id: "cmu",
    title: "Carnegie Mellon",
    tag: "Target",
    imgUrl: "https://images.unsplash.com/photo-1607237138185-eedd9c632b0b?w=480&q=80&auto=format&fit=crop",
    imgCredit: "Unsplash",
    topic: null,
  },
  {
    id: "uoft",
    title: "U of Toronto",
    tag: "Target",
    imgUrl: "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=480&q=80&auto=format&fit=crop",
    imgCredit: "Unsplash",
    topic: null,
  },
  {
    id: "prog",
    title: "MS Computer Science",
    subtitle: "Carnegie Mellon",
    imgUrl: "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=480&q=80&auto=format&fit=crop",
    imgCredit: "Unsplash",
    topic: "schools",
  },
  {
    id: "evt",
    title: "CMU info session",
    subtitle: "Dec 2 · virtual",
    imgUrl: "https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=480&q=80&auto=format&fit=crop",
    imgCredit: "Unsplash",
    topic: "connect",
  },
] as const;

// International cards
const INTL_CARDS = [
  {
    id: "canada",
    title: "Studying in Canada",
    subtitle: "Country guide",
    imgUrl: "https://images.unsplash.com/photo-1517935706615-2717063c2225?w=480&q=80&auto=format&fit=crop",
    imgCredit: "Unsplash",
  },
] as const;

// Peer cards
const PEER_CARDS = [
  {
    id: "p1",
    name: "Maya Chen",
    program: "CS · CMU",
    imgUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=160&q=80&auto=format&fit=crop",
  },
  {
    id: "p2",
    name: "Liam Park",
    program: "CS · Toronto",
    imgUrl: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=160&q=80&auto=format&fit=crop",
  },
  {
    id: "p3",
    name: "Priya N.",
    program: "ML · UW",
    imgUrl: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=160&q=80&auto=format&fit=crop",
  },
] as const;

// ── Main component ─────────────────────────────────────────────────────────

export default function NewSessionLauncher({ recentSession, onSessionStart }: Props) {
  const [inputValue, setInputValue] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const uploadBtnRef = useRef<HTMLButtonElement>(null);

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ["chat-templates"],
    queryFn: getChatTemplates,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const createMut = useMutation({
    mutationFn: createSession,
    onSuccess: (s: ChatSession, vars) => {
      onSessionStart(s.id, vars.origin_kind, vars.origin_ref ?? undefined);
    },
  });

  function startSession(title: string, topicKey?: string) {
    createMut.mutate({
      title: title || "New session",
      topic_key: topicKey ?? null,
      origin_kind: "manual",
    });
  }

  function handleSubmit() {
    const text = inputValue.trim();
    if (!text || createMut.isPending) return;
    setInputValue("");
    startSession(text);
  }

  function handleTemplatePick(tmpl: ChatTemplate) {
    if (createMut.isPending) return;
    createMut.mutate({
      title: tmpl.title,
      topic_key: tmpl.topic,
      origin_kind: "template",
      origin_ref: tmpl.key,
    });
  }

  return (
    <div className="flex-1 overflow-y-auto min-h-0">
      <div className="max-w-[880px] mx-auto px-6 pt-10 pb-14 xl:px-8">

        {/* Hero */}
        <div className="flex items-center gap-3.5 mb-6">
          <UniOrb size={48} />
          <h2 className="text-[28px] font-bold leading-snug text-foreground m-0">
            Where would you like to start?
          </h2>
        </div>

        {/* Input bar */}
        <div className="flex items-center gap-3 border border-border rounded-[14px] bg-card px-4 py-[13px] shadow-[0_1px_2px_rgba(10,20,40,.06),0_1px_1px_rgba(10,20,40,.04)] mb-9">
          {/* Upload "+" — borderless icon, not a boxed button */}
          <button
            ref={uploadBtnRef}
            aria-label="Upload or attach"
            onClick={() => setUploadOpen((v) => !v)}
            className="w-[34px] h-[34px] rounded-[9px] flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-secondary transition-colors shrink-0"
          >
            <Plus size={21} strokeWidth={1.8} />
          </button>

          {uploadOpen && uploadBtnRef.current && (
            <UploadMenu
              anchor={uploadBtnRef.current.getBoundingClientRect()}
              onClose={() => setUploadOpen(false)}
            />
          )}

          <input
            type="text"
            placeholder="Ask me anything, or pick something below"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSubmit();
            }}
            className="flex-1 border-none outline-none text-[16px] bg-transparent text-foreground placeholder:text-muted-foreground"
            aria-label="Start a new session"
          />

          {/* Send button */}
          <button
            aria-label="Send"
            onClick={handleSubmit}
            disabled={!inputValue.trim() || createMut.isPending}
            className="w-9 h-9 rounded-[10px] bg-secondary text-white flex items-center justify-center shrink-0 transition-opacity disabled:opacity-40 hover:bg-secondary/90"
          >
            <ArrowUp size={18} strokeWidth={2.2} />
          </button>
        </div>

        {/* Continue — most-recent session */}
        {recentSession && (
          <section className="mb-7" aria-label="Continue previous session">
            <EyebrowLabel>Continue</EyebrowLabel>
            <ContinueCard
              title={recentSession.title}
              stage={recentSession.stage}
              onClick={() => onSessionStart(recentSession.id, "manual")}
            />
          </section>
        )}

        {/* For you — action cards */}
        <section className="mb-7" aria-label="For you">
          <EyebrowLabel>For you</EyebrowLabel>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <ActionCard
              icon={<List size={20} strokeWidth={1.7} />}
              title="Build your school list"
              onClick={() => startSession("Build your school list", "schools")}
            />
            <ActionCard
              icon={<BookOpen size={20} strokeWidth={1.7} />}
              title="Prep your statement"
              onClick={() => startSession("Prep your statement", "prepare")}
            />
            <ActionCard
              icon={<Scale size={20} strokeWidth={1.7} />}
              title="Compare your schools"
              onClick={() => startSession("Compare your schools", "schools")}
            />
            <ActionCard
              icon={<Heart size={20} strokeWidth={1.7} />}
              title="What you need to thrive"
              onClick={() => startSession("What you need to thrive", "needs")}
            />
          </div>
        </section>

        {/* Academic — representative visual cards */}
        <section className="mb-7" aria-label="Academic">
          <EyebrowLabel>Academic</EyebrowLabel>
          {/* NOTE: Static/representative cards — real school/program/event data
              from the Discover endpoints will be wired in a later slice. */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {ACADEMIC_CARDS.map((c) => (
              <VisualCard
                key={c.id}
                title={c.title}
                subtitle={"subtitle" in c ? c.subtitle : undefined}
                tag={"tag" in c ? c.tag : undefined}
                imgUrl={c.imgUrl}
                imgCredit={c.imgCredit}
                onClick={() =>
                  startSession(c.title, c.topic ?? undefined)
                }
              />
            ))}
          </div>
        </section>

        {/* Financial — scholarship card + action cards */}
        <section className="mb-7" aria-label="Financial">
          <EyebrowLabel>Financial</EyebrowLabel>
          {/* NOTE: Static/representative — real scholarship data from the
              Discover/Financial endpoint will be wired in a later slice. */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <ScholarshipCard
              name="Merit award — you may qualify"
              amount="$5,000/yr"
              note="Scholarships matched to your profile"
              onClick={() => startSession("Scholarships you qualify for", "needs")}
            />
            <ActionCard
              icon={<BookOpen size={20} strokeWidth={1.7} />}
              title="Find more scholarships"
              goldAccent
              onClick={() => startSession("Find more scholarships", "needs")}
            />
            <ActionCard
              icon={<Scale size={20} strokeWidth={1.7} />}
              title="How funding works"
              onClick={() => startSession("How funding works", "needs")}
            />
            <ActionCard
              icon={<Scale size={20} strokeWidth={1.7} />}
              title="Estimate your net cost"
              onClick={() => startSession("Estimate your net cost", "needs")}
            />
          </div>
        </section>

        {/* International — guide + country cards */}
        <section className="mb-7" aria-label="International">
          <EyebrowLabel>International</EyebrowLabel>
          {/* NOTE: Static/representative. */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <ActionCard
              icon={<Compass size={20} strokeWidth={1.7} />}
              title="Student visa basics"
              onClick={() => startSession("Student visa basics", "prepare")}
            />
            <VisualCard
              title="Studying in Canada"
              subtitle="Country guide"
              imgUrl={INTL_CARDS[0].imgUrl}
              imgCredit={INTL_CARDS[0].imgCredit}
              onClick={() => startSession("Studying in Canada", "strategy")}
            />
            <ActionCard
              icon={<BookOpen size={20} strokeWidth={1.7} />}
              title="English test prep"
              onClick={() => startSession("English test prep", "prepare")}
            />
            <ActionCard
              icon={<Compass size={20} strokeWidth={1.7} />}
              title="Credential evaluation"
              onClick={() => startSession("Credential evaluation", "prepare")}
            />
          </div>
        </section>

        {/* Peers — peer avatar cards */}
        <section className="mb-7" aria-label="Peers">
          <EyebrowLabel>Peers</EyebrowLabel>
          {/* NOTE: Static/representative — real peer data from the Connect
              endpoints will be wired in a later slice. */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {PEER_CARDS.map((p) => (
              <PeerCard
                key={p.id}
                name={p.name}
                program={p.program}
                imgUrl={p.imgUrl}
                onClick={() => startSession(`Connect with ${p.name}`, "connect")}
              />
            ))}
            <ActionCard
              icon={<Users size={20} strokeWidth={1.7} />}
              title="Find more peers"
              onClick={() => startSession("Find more peers", "connect")}
            />
          </div>
        </section>

        {/* Start from a template */}
        <section aria-label="Start from a template">
          <EyebrowLabel>Start from a template</EyebrowLabel>
          {templatesLoading ? (
            <div className="flex flex-wrap gap-2 animate-pulse">
              {[120, 140, 110, 130, 100, 150].map((w, i) => (
                <div key={i} className="h-9 rounded-full bg-muted" style={{ width: w }} />
              ))}
            </div>
          ) : templates && templates.length > 0 ? (
            <TemplatesSection templates={templates} onPick={handleTemplatePick} />
          ) : (
            <p className="text-[13px] text-muted-foreground">No templates available.</p>
          )}
        </section>

      </div>
    </div>
  );
}
