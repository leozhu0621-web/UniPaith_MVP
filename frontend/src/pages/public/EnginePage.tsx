import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import AnimatedCounter from '@/components/landing/AnimatedCounter'
import {
  Brain,
  MessageSquare,
  Search,
  RefreshCw,
  Target,
  ClipboardList,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Lock,
  Eye,
  Users,
  Zap,
  Database,
  FileCheck,
  Pencil,
  ChevronRight,
} from 'lucide-react'

/* ── Architecture pipeline steps ── */
const pipelineSteps = [
  {
    icon: MessageSquare,
    title: 'Student Input',
    desc: 'Natural conversation captures goals, constraints, and context.',
  },
  {
    icon: Search,
    title: 'Intent & Entity Parse',
    desc: 'Extract meaning, entities, and implicit preferences from each message.',
  },
  {
    icon: RefreshCw,
    title: 'State Update',
    desc: 'Merge new data into the running student profile and requirement model.',
  },
  {
    icon: Target,
    title: 'Issue & Demand Diagnosis',
    desc: 'Detect gaps, conflicts, and under-specified domains in real time.',
  },
  {
    icon: ClipboardList,
    title: 'Requirement Extraction',
    desc: 'Translate conversation into structured must-haves and preferences.',
  },
  {
    icon: BarChart3,
    title: 'Confidence Scoring',
    desc: 'Calculate multi-dimensional readiness across coverage, consistency, and evidence.',
  },
  {
    icon: ArrowRight,
    title: 'Next Action & Response',
    desc: 'Decide what to ask next or when to deliver recommendations.',
  },
]

/* ── Conversation question types ── */
const questionTypes = [
  {
    title: 'Open Reflection',
    purpose: 'Broad intent capture',
    example: '"What matters most to you in your graduate experience?"',
    whyAsked: 'Surfaces priorities the student may not have articulated yet.',
    impactHint: 'Shapes the initial requirement skeleton and priority weights.',
  },
  {
    title: 'Structured Choice',
    purpose: 'Force tradeoff clarity',
    example: '"If you had to choose: lower cost or higher ranking?"',
    whyAsked: 'Resolves ambiguity when two preferences conflict.',
    impactHint: 'Directly adjusts priority weighting in the scoring model.',
  },
  {
    title: 'Numeric Constraint',
    purpose: 'Budget, score, timeline',
    example: '"What is your maximum annual budget including living costs?"',
    whyAsked: 'Hard constraints that filter the program universe.',
    impactHint: 'Sets elimination thresholds for the matching algorithm.',
  },
  {
    title: 'Evidence Request',
    purpose: 'Verify uncertain claims',
    example: '"You mentioned research experience — can you describe the project?"',
    whyAsked: 'Converts vague signals into verified profile data.',
    impactHint: 'Increases evidence quality score and match precision.',
  },
  {
    title: 'Confirmation',
    purpose: 'Approve or edit inferred summary',
    example: '"Here\'s what I understand so far. Anything to change?"',
    whyAsked: 'Ensures the model reflects the student\'s actual intent.',
    impactHint: 'Locks in confirmed data and raises confidence level.',
  },
]

/* ── Confidence dimensions ── */
const confidenceDimensions = [
  {
    label: 'Coverage',
    weight: 40,
    desc: 'Required fields completed per domain (budget, timeline, eligibility, preferences).',
    color: 'bg-brand-slate-600',
  },
  {
    label: 'Consistency',
    weight: 25,
    desc: 'Absence of unresolved conflicts between stated priorities.',
    color: 'bg-brand-slate-500',
  },
  {
    label: 'Evidence Quality',
    weight: 20,
    desc: 'Explicit and recent confirmations rather than inferred assumptions.',
    color: 'bg-brand-amber-500',
  },
  {
    label: 'Temporal Validity',
    weight: 15,
    desc: 'Freshness of time-sensitive data like test scores, budgets, and deadlines.',
    color: 'bg-brand-amber-400',
  },
]

/* ── Confidence levels ── */
const confidenceLevels = [
  {
    range: '0 - 39',
    label: 'Insufficient',
    desc: 'No shortlist generated. Focused follow-up questions.',
    color: 'bg-red-500',
    width: 'w-[39%]',
  },
  {
    range: '40 - 69',
    label: 'Provisional',
    desc: 'Limited shortlist with explicit warnings on weak areas.',
    color: 'bg-brand-amber-500',
    width: 'w-[30%]',
  },
  {
    range: '70 - 84',
    label: 'Recommendation-ready',
    desc: 'Standard shortlist with full fit rationale.',
    color: 'bg-brand-slate-500',
    width: 'w-[15%]',
  },
  {
    range: '85 - 100',
    label: 'High-confidence',
    desc: 'Full reasoning, stronger ranking, detailed tradeoff analysis.',
    color: 'bg-emerald-500',
    width: 'w-[16%]',
  },
]

/* ── Reason codes ── */
const reasonCodes = [
  'cost_fit',
  'deadline_fit',
  'eligibility_fit',
  'ranking_match',
  'location_pref',
  'program_strength',
]

/* ── Unlock gate requirements ── */
const unlockGates = [
  'Global confidence score >= 70',
  'Budget domain confidence >= 65',
  'Timeline domain confidence >= 65',
  'Eligibility domain confidence >= 65',
  'No unresolved hard conflicts',
  'All required fields for current stage complete',
]

/* ── Trust badges ── */
const trustBadges = [
  { icon: ShieldCheck, label: 'FERPA-Ready' },
  { icon: Lock, label: 'E2E Encrypted' },
  { icon: Users, label: 'Human-in-the-Loop' },
  { icon: FileCheck, label: 'Full Audit Trails' },
  { icon: Eye, label: 'No Black Boxes' },
  { icon: Database, label: 'Student Data Ownership' },
]

export default function EnginePage() {
  return (
    <div className="pt-16">
      {/* ── 1. Hero ── */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-[10%] w-72 h-72 bg-brand-slate-100/60 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-brand-amber-100/40 rounded-full blur-3xl animate-float-slow" />
        </div>

        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <span className="inline-flex items-center gap-2 bg-brand-slate-50 text-brand-slate-700 rounded-full px-5 py-2 text-sm font-medium mb-8">
              <Brain size={14} /> AI Engine
            </span>
          </ScrollReveal>

          <ScrollReveal delay={200} variant="scale-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-[1.1] mb-6 tracking-tight font-heading">
              Intelligence You{' '}
              <span className="text-brand-slate-600">Can Trust</span>
            </h1>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              The intelligence behind every match, every recommendation, every insight.
              Transparent by design.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                size="lg"
                className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white"
                asChild
              >
                <Link to="/signup">
                  Get Started Free
                  <ArrowRight size={20} className="ml-2" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-base px-10 py-7 rounded-xl text-lg"
                asChild
              >
                <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 2. Architecture overview ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                How the engine works
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                Seven connected stages turn natural conversation into actionable, explainable recommendations.
              </p>
            </div>
          </ScrollReveal>

          <div className="flex flex-wrap justify-center items-start gap-3 lg:gap-0">
            {pipelineSteps.map((step, i) => (
              <ScrollReveal key={i} delay={i * 80} variant="fade-up">
                <div className="flex items-center">
                  <div className="w-36 sm:w-40 flex flex-col items-center text-center">
                    <div className="w-16 h-16 rounded-2xl bg-brand-slate-600 text-white flex items-center justify-center mb-3 shadow-md">
                      <step.icon size={26} />
                    </div>
                    <h3 className="text-sm font-bold text-foreground mb-1 font-heading leading-tight">
                      {step.title}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-snug px-1">
                      {step.desc}
                    </p>
                  </div>
                  {i < pipelineSteps.length - 1 && (
                    <div className="hidden lg:flex items-center px-1 mt-[-2.5rem]">
                      <ChevronRight size={20} className="text-brand-slate-300" />
                    </div>
                  )}
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. Conversation engine ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-flex items-center gap-1.5 bg-brand-amber-50 text-brand-amber-700 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <MessageSquare size={14} /> Conversation Engine
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                Progressive diagnosis, not interrogation
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                Five question types adapt to what you have said, what is missing, and what conflicts need resolution.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {questionTypes.map((qt, i) => (
              <ScrollReveal key={i} delay={i * 100} variant="fade-up">
                <div className="bg-card rounded-2xl border p-6 hover:shadow-md transition-all h-full group">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-8 h-8 rounded-lg bg-brand-slate-100 text-brand-slate-600 flex items-center justify-center text-sm font-bold">
                      {i + 1}
                    </span>
                    <h3 className="text-base font-bold text-foreground font-heading">{qt.title}</h3>
                  </div>
                  <p className="text-xs text-brand-slate-500 font-medium uppercase tracking-wide mb-2">
                    {qt.purpose}
                  </p>
                  <p className="text-sm text-muted-foreground italic mb-4">{qt.example}</p>
                  <div className="space-y-2 text-xs">
                    <div className="flex gap-2">
                      <span className="text-brand-slate-500 font-semibold shrink-0">Why asked:</span>
                      <span className="text-muted-foreground">{qt.whyAsked}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-brand-amber-600 font-semibold shrink-0">Impact:</span>
                      <span className="text-muted-foreground">{qt.impactHint}</span>
                    </div>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal delay={600}>
            <div className="bg-brand-slate-50 rounded-2xl border border-brand-slate-200 p-8">
              <h3 className="text-lg font-bold text-foreground mb-4 font-heading">
                Adaptive branching
              </h3>
              <div className="grid sm:grid-cols-3 gap-6">
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-brand-amber-500 mt-2 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">Data insufficient</p>
                    <p className="text-xs text-muted-foreground">Focused follow-up question targeting the weakest domain.</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-brand-slate-500 mt-2 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">Conflict detected</p>
                    <p className="text-xs text-muted-foreground">Explicit tradeoff card presented for student resolution.</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-brand-slate-300 mt-2 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">Ambiguity persists</p>
                    <p className="text-xs text-muted-foreground">Mini-form fallback for structured data capture.</p>
                  </div>
                </div>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 4. Confidence scoring ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-flex items-center gap-1.5 bg-brand-slate-100 text-brand-slate-700 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <BarChart3 size={14} /> Scoring
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                Confidence you can see
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                A four-dimension scoring model you can inspect, understand, and improve.
              </p>
            </div>
          </ScrollReveal>

          {/* Dimension cards */}
          <div className="grid sm:grid-cols-2 gap-6 mb-16">
            {confidenceDimensions.map((dim, i) => (
              <ScrollReveal key={i} delay={i * 100} variant="fade-up">
                <div className="bg-card rounded-2xl border p-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-bold text-foreground font-heading">{dim.label}</h3>
                    <span className="text-sm font-bold text-brand-slate-600">
                      <AnimatedCounter end={dim.weight} suffix="%" />
                    </span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full mb-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${dim.color} transition-all duration-1000`}
                      style={{ width: `${dim.weight}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground">{dim.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>

          {/* Confidence level scale */}
          <ScrollReveal delay={500}>
            <div className="bg-card rounded-2xl border p-8">
              <h3 className="text-lg font-bold text-foreground mb-6 font-heading">
                Confidence levels
              </h3>
              <div className="flex w-full h-4 rounded-full overflow-hidden mb-6">
                {confidenceLevels.map((level, i) => (
                  <div
                    key={i}
                    className={`${level.color} ${level.width} ${i === 0 ? 'rounded-l-full' : ''} ${i === confidenceLevels.length - 1 ? 'rounded-r-full' : ''}`}
                  />
                ))}
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {confidenceLevels.map((level, i) => (
                  <div key={i} className="flex gap-3">
                    <div className={`w-3 h-3 rounded-full ${level.color} mt-1 shrink-0`} />
                    <div>
                      <p className="text-sm font-bold text-foreground">{level.range}</p>
                      <p className="text-xs font-medium text-brand-slate-600 mb-0.5">{level.label}</p>
                      <p className="text-xs text-muted-foreground">{level.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 5. Explainability ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                Every recommendation has a receipt
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                No black boxes. Every program recommendation comes with a full breakdown of why it was chosen.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <ScrollReveal delay={100} variant="fade-left">
              <div className="bg-card rounded-2xl border p-8 h-full">
                <h3 className="text-lg font-bold text-foreground mb-6 font-heading">
                  What comes with each recommendation
                </h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 size={18} className="text-emerald-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-foreground">Matched requirements</p>
                      <p className="text-xs text-muted-foreground">
                        Green checks for every requirement the program satisfies.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertTriangle size={18} className="text-brand-amber-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-foreground">Unmet or uncertain requirements</p>
                      <p className="text-xs text-muted-foreground">
                        Amber warnings for gaps, unknowns, or weak-signal matches.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <BarChart3 size={18} className="text-brand-slate-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-foreground">Confidence level and improvement path</p>
                      <p className="text-xs text-muted-foreground">
                        Your current confidence score and exactly what to provide to raise it.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <FileCheck size={18} className="text-brand-slate-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-foreground">Reason codes</p>
                      <p className="text-xs text-muted-foreground">
                        Structured tags for each fit dimension.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mt-6">
                  {reasonCodes.map((code) => (
                    <span
                      key={code}
                      className="inline-block bg-brand-slate-50 text-brand-slate-600 text-xs font-mono px-2.5 py-1 rounded-md border border-brand-slate-200"
                    >
                      {code}
                    </span>
                  ))}
                </div>
              </div>
            </ScrollReveal>

            <ScrollReveal delay={200} variant="fade-right">
              <div className="bg-card rounded-2xl border p-8 h-full flex flex-col">
                <h3 className="text-lg font-bold text-foreground mb-6 font-heading">
                  Every inference is editable
                </h3>
                <div className="flex-1 flex flex-col justify-center">
                  <div className="bg-brand-slate-50 rounded-xl border border-brand-slate-200 p-6 mb-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Pencil size={14} className="text-brand-slate-500" />
                      <span className="text-xs font-medium text-brand-slate-600 uppercase tracking-wide">
                        AI Inference
                      </span>
                    </div>
                    <p className="text-sm text-foreground mb-4">
                      "Based on your GPA and research mentions, I'm estimating your competitiveness
                      for top-20 programs as moderate."
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs px-3 py-1.5 rounded-lg border border-emerald-200 cursor-pointer hover:bg-emerald-100 transition-colors">
                        <CheckCircle2 size={12} /> Accept
                      </span>
                      <span className="inline-flex items-center gap-1 bg-red-50 text-red-700 text-xs px-3 py-1.5 rounded-lg border border-red-200 cursor-pointer hover:bg-red-100 transition-colors">
                        <AlertTriangle size={12} /> Reject
                      </span>
                      <span className="inline-flex items-center gap-1 bg-brand-amber-50 text-brand-amber-700 text-xs px-3 py-1.5 rounded-lg border border-brand-amber-200 cursor-pointer hover:bg-brand-amber-100 transition-colors">
                        <Pencil size={12} /> Modify
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Accept, reject, or modify any assumption the engine makes. Your corrections
                    feed back into the model immediately, improving every future recommendation.
                  </p>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* ── 6. Shortlist unlock ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-slate-900">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-12">
              <span className="inline-flex items-center gap-1.5 bg-brand-amber-500/20 text-brand-amber-300 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <Lock size={14} /> Quality Gate
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 font-heading">
                Gated quality, not gated access
              </h2>
              <p className="text-brand-slate-300 max-w-2xl mx-auto text-lg">
                We don't show you programs until we're confident the match is meaningful.
                And we tell you exactly what's missing to get there.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="bg-brand-slate-800 rounded-2xl border border-brand-slate-700 p-8">
              <h3 className="text-base font-bold text-white mb-6 font-heading">
                Shortlist unlock requires all of the following:
              </h3>
              <div className="grid sm:grid-cols-2 gap-4">
                {unlockGates.map((gate, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <CheckCircle2 size={16} className="text-brand-amber-400 shrink-0" />
                    <span className="text-sm text-brand-slate-200">{gate}</span>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <p className="text-center text-brand-slate-400 mt-8 text-sm max-w-xl mx-auto">
              When any gate is unmet, the engine tells you exactly which domain needs more
              information and what questions will close the gap.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 7. Flywheel / network effect ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                The network effect
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                Every student profile, every application, every institution interaction makes the engine
                smarter for everyone.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="relative max-w-lg mx-auto">
              {/* Circular flywheel */}
              <div className="relative w-72 h-72 sm:w-80 sm:h-80 mx-auto">
                {/* Orbit ring */}
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-brand-slate-200" />
                <div className="absolute inset-4 rounded-full border border-brand-slate-100" />

                {/* Center */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-20 h-20 rounded-full bg-brand-slate-600 text-white flex items-center justify-center shadow-lg">
                    <Zap size={28} />
                  </div>
                </div>

                {/* Node: More Participation — top */}
                <div className="absolute -top-6 left-1/2 -translate-x-1/2">
                  <div className="bg-card rounded-xl border shadow-sm px-4 py-3 text-center w-40">
                    <Users size={18} className="text-brand-slate-600 mx-auto mb-1" />
                    <p className="text-xs font-bold text-foreground">More Participation</p>
                  </div>
                </div>

                {/* Node: Better Data — bottom-right */}
                <div className="absolute -bottom-4 -right-8 sm:-right-4">
                  <div className="bg-card rounded-xl border shadow-sm px-4 py-3 text-center w-40">
                    <Database size={18} className="text-brand-amber-500 mx-auto mb-1" />
                    <p className="text-xs font-bold text-foreground">Better Data</p>
                  </div>
                </div>

                {/* Node: Smarter AI — bottom-left */}
                <div className="absolute -bottom-4 -left-8 sm:-left-4">
                  <div className="bg-card rounded-xl border shadow-sm px-4 py-3 text-center w-40">
                    <Brain size={18} className="text-brand-slate-500 mx-auto mb-1" />
                    <p className="text-xs font-bold text-foreground">Smarter AI</p>
                  </div>
                </div>

                {/* Arrows: curved connecting lines via SVG */}
                <svg
                  className="absolute inset-0 w-full h-full"
                  viewBox="0 0 320 320"
                  fill="none"
                >
                  {/* Top to bottom-right */}
                  <path
                    d="M185 50 Q 290 110 260 240"
                    stroke="#C9D3E8"
                    strokeWidth="2"
                    strokeDasharray="6 4"
                    fill="none"
                    markerEnd="url(#arrowhead)"
                  />
                  {/* Bottom-right to bottom-left */}
                  <path
                    d="M240 270 Q 160 340 80 270"
                    stroke="#C9D3E8"
                    strokeWidth="2"
                    strokeDasharray="6 4"
                    fill="none"
                    markerEnd="url(#arrowhead)"
                  />
                  {/* Bottom-left to top */}
                  <path
                    d="M60 240 Q 30 110 135 50"
                    stroke="#C9D3E8"
                    strokeWidth="2"
                    strokeDasharray="6 4"
                    fill="none"
                    markerEnd="url(#arrowhead)"
                  />
                  <defs>
                    <marker
                      id="arrowhead"
                      markerWidth="8"
                      markerHeight="6"
                      refX="8"
                      refY="3"
                      orient="auto"
                    >
                      <path d="M0 0 L8 3 L0 6 Z" fill="#A3B3D4" />
                    </marker>
                  </defs>
                </svg>
              </div>

              <div className="mt-12 text-center">
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  More participation produces richer data. Richer data trains smarter models.
                  Smarter models deliver better outcomes. Better outcomes attract more participation.
                </p>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 8. Trust architecture ── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-2xl sm:text-3xl font-bold text-center text-foreground mb-10 font-heading">
              Built on trust
            </h2>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {trustBadges.map((badge, i) => (
                <div
                  key={i}
                  className="bg-card rounded-2xl border p-5 flex flex-col items-center text-center hover:shadow-md transition-shadow"
                >
                  <badge.icon size={24} className="text-brand-slate-600 mb-2" />
                  <span className="text-xs font-bold text-foreground">{badge.label}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── 9. CTA ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-brand-slate-700 to-brand-slate-900">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 font-heading">
              See the engine in action
            </h2>
            <p className="text-brand-slate-300 mb-10 text-lg max-w-xl mx-auto">
              Whether you are a student exploring programs or an institution optimizing admissions,
              the engine works for you.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                size="lg"
                className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white"
                asChild
              >
                <Link to="/signup">
                  Get Started Free
                  <ArrowRight size={20} className="ml-2" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-base px-10 py-7 rounded-xl text-lg border-brand-slate-500 text-white hover:bg-brand-slate-800 hover:text-white"
                asChild
              >
                <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
