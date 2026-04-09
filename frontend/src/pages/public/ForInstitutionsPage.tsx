import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import AnimatedCounter from '@/components/landing/AnimatedCounter'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import {
  ArrowRight, X, Check, KanbanSquare, ListChecks, UserCircle, Video,
  MessageSquare, Users, Megaphone, CalendarDays, BarChart3, Upload,
  Brain, ShieldCheck, Zap, AlertTriangle, Shield, Lock, BookOpen,
  FileCheck, UserCog, Building2,
} from 'lucide-react'

/* ── Before / After comparison rows ── */
const comparisons = [
  { before: 'Manual review of thousands of applications per cycle', after: 'AI-prioritized queue with rubric-aligned summaries' },
  { before: 'Inconsistent application formats across channels', after: 'Standardized structured profiles with verified documents' },
  { before: 'Fragmented communication across email, portals, phone', after: 'Unified inbox with application-linked messaging' },
  { before: 'Guessing at pipeline health and conversion rates', after: 'Real-time analytics dashboard with funnel insights' },
  { before: 'Compliance gaps and manual audit preparation', after: 'Built-in verification, anomaly detection, audit trails' },
]

/* ── Feature deep-dive cards ── */
const platformFeatures = [
  { icon: KanbanSquare, title: 'Pipeline Board', desc: 'Discovered through Enrolled stages. Drag-and-drop applicants across your custom pipeline with real-time status tracking.' },
  { icon: ListChecks, title: 'Review Queue', desc: 'AI-prioritized applicant queue with rubric-aligned summaries. Focus reviewer time on the candidates that matter most.' },
  { icon: UserCircle, title: 'Student Detail', desc: 'Full student profile with AI fit analysis, scoring breakdown, and document verification status at a glance.' },
  { icon: Video, title: 'Interview Management', desc: 'Schedule, track, and score interviews. AI-generated recommendations based on rubric alignment and conversation signals.' },
  { icon: MessageSquare, title: 'Messaging Hub', desc: 'Unified inbox with templates, bulk actions, and campaign-linked threads. Every message tied to an application record.' },
  { icon: Users, title: 'Segments Builder', desc: 'Visual criteria builder: GPA range, region, test scores, program interest. Build cohorts in clicks, not spreadsheets.' },
  { icon: Megaphone, title: 'Campaign Tools', desc: 'Targeted email outreach with performance tracking. A/B test subject lines, monitor open rates, and measure conversions.' },
  { icon: CalendarDays, title: 'Events Manager', desc: 'Webinars, campus visits, info sessions. Manage RSVPs, send reminders, and track attendance to pipeline impact.' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Funnel conversion, yield trends, demographic breakdowns. Real-time data to inform strategy, not end-of-cycle reports.' },
  { icon: Upload, title: 'Data Upload', desc: 'Bulk import from existing systems. CSV, Excel, or direct API integration. Migrate your historical data without disruption.' },
]

/* ── AI capability cards ── */
const aiCapabilities = [
  { icon: Zap, title: 'AI Triage', desc: 'Automatically sort incoming applications by fit score, flagging high-priority candidates and routing them to the right reviewer.', note: 'Human reviewers make all final decisions.' },
  { icon: Brain, title: 'Score Suggestions', desc: 'Rubric-aligned scoring recommendations based on profile analysis. AI highlights strengths and gaps against your criteria.', note: 'Suggestions only — your team assigns final scores.' },
  { icon: BarChart3, title: 'Match Quality', desc: 'Predict yield probability and enrollment likelihood per applicant. Optimize outreach spend on candidates most likely to enroll.', note: 'Predictions improve with your historical data.' },
  { icon: AlertTriangle, title: 'Anomaly Detection', desc: 'Flag inconsistencies in transcripts, test scores, and documents. Surface integrity concerns before they reach committee review.', note: 'Flags for review — never auto-rejects.' },
]

/* ── Compliance badges ── */
const complianceBadges = [
  { icon: Shield, label: 'FERPA Compliant' },
  { icon: Lock, label: 'GDPR Ready' },
  { icon: BookOpen, label: 'Audit Trails' },
  { icon: UserCog, label: 'Role-Based Access' },
  { icon: FileCheck, label: 'Doc Verification' },
  { icon: ShieldCheck, label: 'SOC 2 Ready' },
]

/* ── FAQ ── */
const faqs = [
  { q: 'Do we need to replace our current CRM?', a: 'No. UniPaith is integration-first. We feed structured data and AI-prioritized pipeline insights into your existing CRM — Slate, Salesforce, or whatever you use. No rip-and-replace required.' },
  { q: 'How long does setup take?', a: 'Days, not months. Most institutions are operational within a week. We handle data migration, configure your pipeline stages, and train your team. No 6-18 month procurement cycle.' },
  { q: 'How is this different from Element451 or EAB Navigate?', a: 'UniPaith is two-sided. Students build profiles and discover your programs through AI matching — you get pre-structured, verified applicant data instead of raw form submissions. It\'s a marketplace, not just a CRM.' },
  { q: 'How does AI scoring work?', a: 'AI generates scoring suggestions aligned to your rubric criteria. It highlights strengths and gaps, but your admissions team always makes the final determination. Every AI output is explainable and auditable.' },
  { q: 'What\'s the pricing model?', a: 'Usage-based pricing tied to pipeline volume. No multi-year contracts, no long procurement processes. Start with a pilot and scale when you see results.' },
  { q: 'Is student data safe?', a: 'Yes. FERPA-compliant, GDPR-ready, with end-to-end encryption, role-based access controls, and full audit trails. Student data is never shared without explicit consent, and you can request deletion at any time.' },
]

export default function ForInstitutionsPage() {
  return (
    <div className="pt-16">
      {/* ── Hero ── */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-[10%] w-72 h-72 bg-brand-slate-100/60 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-brand-amber-100/30 rounded-full blur-3xl animate-float-slow" />
        </div>

        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <span className="inline-flex items-center gap-2 bg-brand-slate-100 text-brand-slate-700 rounded-full px-5 py-2 text-sm font-medium mb-8">
              <Building2 size={14} /> For Institutions
            </span>
          </ScrollReveal>

          <ScrollReveal delay={200} variant="scale-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-[1.1] mb-6 tracking-tight font-heading">
              The admissions operating system{' '}
              <br className="hidden sm:block" />
              <span className="text-brand-slate-600">your team deserves.</span>
            </h1>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              AI-powered pipeline management. Structured applicant data from day one. Review, communicate, analyze, and enroll — in one workspace built for admissions teams.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-slate-600 hover:bg-brand-slate-700 text-white" asChild>
                <Link to="/signup?role=institution_admin">
                  Schedule a Demo
                  <ArrowRight size={20} className="ml-2" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
                <a href="#features">See Features</a>
              </Button>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={800}>
            <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-10 text-sm text-muted-foreground/60">
              <span>No procurement cycle</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>Live in days</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>Works with your CRM</span>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Pain section ── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4 font-heading">
              Admissions operations are under pressure
            </h2>
            <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto text-lg">
              More applications. Fewer staff. Outdated tools. The math doesn't work.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-slate-600 font-heading mb-1"><AnimatedCounter end={50} suffix="K+" /></div>
                <p className="text-sm text-muted-foreground">applications per cycle at top institutions</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-amber-500 font-heading mb-1"><AnimatedCounter end={30} suffix=" min" /></div>
                <p className="text-sm text-muted-foreground">avg manual review time per application</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-slate-600 font-heading mb-1"><AnimatedCounter end={23} suffix="%" /></div>
                <p className="text-sm text-muted-foreground">staff reduction in admissions offices since 2019</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-amber-500 font-heading mb-1">6-18 mo</div>
                <p className="text-sm text-muted-foreground">typical procurement cycle for new admissions tools</p>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-card rounded-2xl border p-8">
                <p className="text-muted-foreground leading-relaxed italic">
                  "We reviewed 12,000 applications last cycle with a team of six. By March, everyone was burned out. We know we're missing qualified candidates, but there's no time to read every file carefully."
                </p>
                <p className="text-sm text-muted-foreground/60 mt-4">-- Director of Admissions, Regional University</p>
              </div>
              <div className="bg-card rounded-2xl border p-8">
                <p className="text-muted-foreground leading-relaxed italic">
                  "Our CRM tracks contacts, not pipeline. We have no real-time view of conversion rates, no funnel analytics. Every board report is a manual spreadsheet exercise that takes two weeks."
                </p>
                <p className="text-sm text-muted-foreground/60 mt-4">-- VP Enrollment Management, Liberal Arts College</p>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Before / After comparison ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                Before UniPaith vs. after
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">
                See the operational difference across every dimension of your admissions workflow.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="bg-card rounded-2xl border overflow-hidden">
              {/* Header */}
              <div className="grid grid-cols-[1fr_1fr] divide-x divide-border bg-muted/50">
                <div className="px-6 py-4 text-center">
                  <span className="font-semibold text-muted-foreground text-sm uppercase tracking-wide">Before</span>
                </div>
                <div className="px-6 py-4 text-center">
                  <span className="font-semibold text-brand-slate-600 text-sm uppercase tracking-wide">With UniPaith</span>
                </div>
              </div>

              {/* Rows */}
              {comparisons.map((row, i) => (
                <div key={i} className="grid grid-cols-[1fr_1fr] divide-x divide-border border-t">
                  <div className="px-6 py-5 flex items-start gap-3">
                    <X size={18} className="text-destructive flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-muted-foreground leading-relaxed">{row.before}</span>
                  </div>
                  <div className="px-6 py-5 flex items-start gap-3">
                    <Check size={18} className="text-brand-slate-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-foreground leading-relaxed">{row.after}</span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Feature deep-dive ── */}
      <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-block bg-brand-slate-100 text-brand-slate-700 text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
                Platform
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                One workspace. Ten capabilities.
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">
                Every tool your admissions team needs — integrated, not bolted on.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {platformFeatures.map((f, i) => (
              <ScrollReveal key={i} delay={i * 80} variant="fade-up">
                <div className="bg-card rounded-2xl border p-7 hover:shadow-md transition-all h-full group">
                  <div className="w-12 h-12 rounded-xl bg-brand-slate-100 flex items-center justify-center mb-5">
                    <f.icon className="text-brand-slate-600 transition-transform duration-300 group-hover:scale-110" size={24} />
                  </div>
                  <h3 className="text-lg font-bold text-foreground mb-2 font-heading">{f.title}</h3>
                  <p className="text-muted-foreground leading-relaxed text-sm">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Integration section ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 font-heading">
                Works alongside your existing tools
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                No rip-and-replace. UniPaith feeds your existing CRM with structured data and AI-prioritized pipeline.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="flex flex-col md:flex-row items-center justify-center gap-6">
              {/* Existing tools */}
              <div className="flex flex-col gap-4 w-full md:w-auto">
                {['Slate', 'Salesforce', 'Your SIS'].map((tool, i) => (
                  <div key={i} className="bg-card rounded-xl border px-6 py-4 text-center md:text-left min-w-[160px]">
                    <span className="text-sm font-medium text-muted-foreground">{tool}</span>
                  </div>
                ))}
              </div>

              {/* Connector arrows */}
              <div className="flex md:flex-col items-center gap-2 py-4 md:py-0 md:px-4">
                <div className="w-12 h-0.5 md:w-0.5 md:h-12 bg-border" />
                <div className="w-8 h-0.5 md:w-0.5 md:h-8 bg-border" />
                <div className="w-12 h-0.5 md:w-0.5 md:h-12 bg-border" />
              </div>

              {/* UniPaith hub */}
              <div className="bg-brand-slate-600 rounded-2xl px-10 py-8 text-center shadow-lg">
                <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-3">
                  <Zap size={28} className="text-brand-amber-400" />
                </div>
                <span className="text-white font-bold text-lg font-heading">UniPaith</span>
                <p className="text-brand-slate-300 text-xs mt-1">AI-powered layer</p>
              </div>

              {/* Connector arrows */}
              <div className="flex md:flex-col items-center gap-2 py-4 md:py-0 md:px-4">
                <div className="w-12 h-0.5 md:w-0.5 md:h-12 bg-border" />
                <div className="w-8 h-0.5 md:w-0.5 md:h-8 bg-border" />
                <div className="w-12 h-0.5 md:w-0.5 md:h-12 bg-border" />
              </div>

              {/* Outputs */}
              <div className="flex flex-col gap-4 w-full md:w-auto">
                {['Structured Profiles', 'AI-Scored Pipeline', 'Analytics & Reports'].map((out, i) => (
                  <div key={i} className="bg-brand-slate-50 rounded-xl border border-brand-slate-200 px-6 py-4 text-center md:text-left min-w-[180px]">
                    <span className="text-sm font-medium text-brand-slate-700">{out}</span>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <p className="text-center text-muted-foreground text-sm mt-12 max-w-lg mx-auto">
              UniPaith sits between your applicant sources and your existing systems — enriching data, prioritizing pipeline, and surfacing insights your CRM can't generate on its own.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* ── AI capabilities (dark section) ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-slate-900">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-flex items-center gap-1.5 bg-brand-amber-500/20 text-brand-amber-300 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <Brain size={14} /> AI-Powered
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 font-heading">
                AI that augments your team
              </h2>
              <p className="text-brand-slate-300 max-w-2xl mx-auto text-lg">
                Every AI capability is designed with human oversight at the center. Suggestions, not decisions. Transparency, not black boxes.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 gap-6">
            {aiCapabilities.map((cap, i) => (
              <ScrollReveal key={i} delay={i * 150} variant="fade-up">
                <div className="bg-brand-slate-800 rounded-2xl border border-brand-slate-700 p-8 h-full">
                  <div className="w-12 h-12 rounded-xl bg-brand-amber-500/15 flex items-center justify-center mb-5">
                    <cap.icon size={24} className="text-brand-amber-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2 font-heading">{cap.title}</h3>
                  <p className="text-brand-slate-300 text-sm leading-relaxed mb-4">{cap.desc}</p>
                  <div className="flex items-center gap-2 text-brand-amber-400/80 text-xs">
                    <ShieldCheck size={14} className="flex-shrink-0" />
                    <span>{cap.note}</span>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Compliance & governance ── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 font-heading">
              Built for compliance from day one
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg mb-12">
              Enterprise-grade security and governance. No afterthoughts.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6">
              {complianceBadges.map((badge, i) => (
                <div key={i} className="flex flex-col items-center gap-3 p-5 bg-card rounded-2xl border">
                  <badge.icon size={28} className="text-brand-slate-500" />
                  <span className="text-xs font-medium text-foreground text-center leading-tight">{badge.label}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-foreground mb-12 font-heading">
              Questions institutions ask
            </h2>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <Accordion type="single" collapsible className="space-y-3">
              {faqs.map((faq, i) => (
                <AccordionItem key={i} value={`faq-${i}`} className="bg-card rounded-xl border px-6">
                  <AccordionTrigger className="text-left font-semibold text-foreground hover:no-underline py-5">
                    {faq.q}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground leading-relaxed pb-5">
                    {faq.a}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </ScrollReveal>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-brand-slate-700 to-brand-slate-900">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 font-heading">
              Transform your admissions operations
            </h2>
            <p className="text-brand-slate-300 mb-10 text-lg max-w-xl mx-auto">
              See how UniPaith can reduce review time, improve yield, and give your team the tools they actually need. No long procurement process required.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <Button size="lg" className="text-base px-12 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup?role=institution_admin">
                Schedule a Demo
                <ArrowRight size={20} className="ml-2" />
              </Link>
            </Button>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
