import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import {
  ArrowRight, X, Check, KanbanSquare, ListChecks, MessageSquare, Users,
  Megaphone, BarChart3, Upload, Brain, ShieldCheck, Zap, AlertTriangle,
  Shield, Lock, BookOpen, FileCheck, UserCog, Building2,
} from 'lucide-react'

const comparisons = [
  { before: 'Manual review of thousands of apps', after: 'AI-prioritized queue with rubric-aligned summaries' },
  { before: 'Inconsistent formats across channels', after: 'Standardized profiles with verified documents' },
  { before: 'Fragmented communication', after: 'Unified inbox with application-linked messaging' },
  { before: 'Guessing at pipeline health', after: 'Real-time analytics with funnel insights' },
  { before: 'Compliance gaps and manual audits', after: 'Built-in verification and audit trails' },
]

const platformFeatures = [
  { icon: KanbanSquare, title: 'Pipeline Board', desc: 'Drag-and-drop applicants across custom pipeline stages with real-time tracking.' },
  { icon: ListChecks, title: 'Review Queue', desc: 'AI-prioritized queue with rubric-aligned summaries. Focus on candidates that matter.' },
  { icon: MessageSquare, title: 'Messaging Hub', desc: 'Unified inbox with templates, bulk actions, and campaign-linked threads.' },
  { icon: Users, title: 'Segments Builder', desc: 'Visual criteria builder: GPA, region, test scores, program interest.' },
  { icon: Megaphone, title: 'Campaign Tools', desc: 'Targeted outreach with A/B testing, open rates, and conversion tracking.' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Funnel conversion, yield trends, demographics — real-time, not end-of-cycle.' },
  { icon: Upload, title: 'Data Upload', desc: 'Bulk import from existing systems. CSV, Excel, or direct API.' },
  { icon: Brain, title: 'AI Triage', desc: 'Auto-sort applications by fit score. Flag high-priority candidates for review.' },
]

const aiCapabilities = [
  { icon: Zap, title: 'AI Triage', desc: 'Sort incoming applications by fit score, routing high-priority candidates to the right reviewer.', note: 'Human reviewers make all final decisions.' },
  { icon: Brain, title: 'Score Suggestions', desc: 'Rubric-aligned scoring recommendations. AI highlights strengths and gaps against your criteria.', note: 'Suggestions only — your team assigns final scores.' },
  { icon: BarChart3, title: 'Yield Prediction', desc: 'Predict enrollment likelihood per applicant. Optimize outreach on candidates most likely to enroll.', note: 'Predictions improve with your historical data.' },
  { icon: AlertTriangle, title: 'Anomaly Detection', desc: 'Flag inconsistencies in transcripts, scores, and documents before they reach committee.', note: 'Flags for review — never auto-rejects.' },
]

const complianceBadges = [
  { icon: Shield, label: 'FERPA' },
  { icon: Lock, label: 'GDPR' },
  { icon: BookOpen, label: 'Audit Trails' },
  { icon: UserCog, label: 'RBAC' },
  { icon: FileCheck, label: 'Doc Verification' },
  { icon: ShieldCheck, label: 'SOC 2 Ready' },
]

const faqs = [
  { q: 'Do we need to replace our current CRM?', a: 'No. UniPaith feeds structured data and AI-prioritized insights into Slate, Salesforce, or whatever you use. No rip-and-replace.' },
  { q: 'How long does setup take?', a: 'Days, not months. Most institutions are live within a week. We handle migration, configuration, and training.' },
  { q: 'How is this different from Element451 or EAB?', a: 'UniPaith is two-sided. Students build profiles and discover your programs through AI matching — you get pre-structured, verified data instead of raw submissions.' },
  { q: 'What does pricing look like?', a: 'Usage-based pricing tied to pipeline volume. No multi-year contracts. Start with a pilot, scale when you see results.' },
]

export default function ForInstitutionsPage() {
  return (
    <div className="pt-16">
      {/* Hero */}
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
              AI admissions operations.{' '}
              <br className="hidden sm:block" />
              <span className="text-brand-slate-600">Built for your team.</span>
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              Structured applicant data from day one. AI-powered pipeline management. Review, communicate, analyze, and enroll — one workspace.
            </p>
          </ScrollReveal>
          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-slate-600 hover:bg-brand-slate-700 text-white" asChild>
                <Link to="/signup?role=institution_admin">Schedule a Demo <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
                <a href="#features">See Features</a>
              </Button>
            </div>
          </ScrollReveal>
          <ScrollReveal delay={800}>
            <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-10 text-sm text-muted-foreground/60">
              <span>Live in days</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>Works with your CRM</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>No procurement cycle</span>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Before / After */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-foreground mb-12 font-heading">Before vs. after UniPaith</h2>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="bg-card rounded-2xl border overflow-hidden">
              <div className="grid grid-cols-2 border-b bg-muted/50">
                <div className="px-6 py-3 text-center"><span className="font-semibold text-muted-foreground text-sm uppercase tracking-wide">Before</span></div>
                <div className="px-6 py-3 text-center"><span className="font-semibold text-brand-slate-600 text-sm uppercase tracking-wide">With UniPaith</span></div>
              </div>
              {comparisons.map((row, i) => (
                <div key={i} className={`grid grid-cols-2 ${i < comparisons.length - 1 ? 'border-b' : ''}`}>
                  <div className="px-5 py-4 flex items-start gap-3"><X size={16} className="text-destructive flex-shrink-0 mt-0.5" /><span className="text-sm text-muted-foreground">{row.before}</span></div>
                  <div className="px-5 py-4 flex items-start gap-3"><Check size={16} className="text-brand-slate-600 flex-shrink-0 mt-0.5" /><span className="text-sm text-foreground">{row.after}</span></div>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">One workspace. Eight capabilities.</h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">Every tool your admissions team needs — integrated, not bolted on.</p>
            </div>
          </ScrollReveal>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {platformFeatures.map((f, i) => (
              <ScrollReveal key={i} delay={i * 60} variant="fade-up">
                <div className="bg-card rounded-xl border p-6 hover:shadow-md transition-all h-full group">
                  <div className="w-10 h-10 rounded-lg bg-brand-slate-100 flex items-center justify-center mb-3">
                    <f.icon className="text-brand-slate-600 group-hover:scale-110 transition-transform" size={20} />
                  </div>
                  <h3 className="text-sm font-bold text-foreground mb-1 font-heading">{f.title}</h3>
                  <p className="text-muted-foreground text-xs leading-relaxed">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
          <ScrollReveal delay={600}>
            <p className="mt-8 text-center text-sm text-muted-foreground italic">Works alongside Slate, Salesforce, and your existing SIS. No rip-and-replace.</p>
          </ScrollReveal>
        </div>
      </section>

      {/* AI capabilities */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-slate-900">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 font-heading">AI that augments your team</h2>
              <p className="text-brand-slate-300 max-w-xl mx-auto text-lg">Suggestions, not decisions. Transparency, not black boxes.</p>
            </div>
          </ScrollReveal>
          <div className="grid md:grid-cols-2 gap-5">
            {aiCapabilities.map((cap, i) => (
              <ScrollReveal key={i} delay={i * 100} variant="fade-up">
                <div className="bg-brand-slate-800 rounded-xl border border-brand-slate-700 p-6 h-full">
                  <div className="w-10 h-10 rounded-lg bg-brand-amber-500/15 flex items-center justify-center mb-3">
                    <cap.icon size={20} className="text-brand-amber-400" />
                  </div>
                  <h3 className="text-base font-bold text-white mb-1.5 font-heading">{cap.title}</h3>
                  <p className="text-brand-slate-300 text-sm mb-3">{cap.desc}</p>
                  <div className="flex items-center gap-2 text-brand-amber-400/80 text-xs">
                    <ShieldCheck size={12} className="flex-shrink-0" /><span>{cap.note}</span>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-10 font-heading">Built for compliance from day one</h2>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
              {complianceBadges.map((badge, i) => (
                <div key={i} className="flex flex-col items-center gap-2 p-4 bg-card rounded-xl border">
                  <badge.icon size={22} className="text-brand-slate-500" />
                  <span className="text-xs font-medium text-foreground">{badge.label}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-center text-foreground mb-10 font-heading">Questions institutions ask</h2>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <Accordion type="single" collapsible className="space-y-3">
              {faqs.map((faq, i) => (
                <AccordionItem key={i} value={`faq-${i}`} className="bg-card rounded-xl border px-6">
                  <AccordionTrigger className="text-left font-semibold text-foreground hover:no-underline py-4 text-sm">{faq.q}</AccordionTrigger>
                  <AccordionContent className="text-muted-foreground text-sm pb-4">{faq.a}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </ScrollReveal>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-brand-slate-700 to-brand-slate-900">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 font-heading">Transform your admissions operations</h2>
            <p className="text-brand-slate-300 mb-10 text-lg max-w-xl mx-auto">Reduce review time, improve yield, give your team the tools they deserve. No long procurement process.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <Button size="lg" className="text-base px-12 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup?role=institution_admin">Schedule a Demo <ArrowRight size={20} className="ml-2" /></Link>
            </Button>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
