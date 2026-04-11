import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import AnimatedCounter from '@/components/landing/AnimatedCounter'
import {
  Brain, MessageSquare, Search, RefreshCw, Target, ClipboardList,
  BarChart3, ArrowRight, ShieldCheck, Lock, Users, Eye, Database,
  FileCheck, ChevronRight,
} from 'lucide-react'

const pipelineSteps = [
  { icon: MessageSquare, title: 'Input', desc: 'Conversation captures goals and constraints.' },
  { icon: Search, title: 'Parse', desc: 'Extract meaning and preferences.' },
  { icon: RefreshCw, title: 'Update', desc: 'Merge into running profile.' },
  { icon: Target, title: 'Diagnose', desc: 'Detect gaps and conflicts.' },
  { icon: ClipboardList, title: 'Extract', desc: 'Build structured requirements.' },
  { icon: BarChart3, title: 'Score', desc: 'Multi-dimensional confidence.' },
  { icon: ArrowRight, title: 'Respond', desc: 'Next question or recommendation.' },
]

const confidenceDimensions = [
  { label: 'Coverage', weight: 40, desc: 'Required fields completed per domain.', color: 'bg-harbor' },
  { label: 'Consistency', weight: 25, desc: 'No unresolved conflicts between priorities.', color: 'bg-harbor' },
  { label: 'Evidence Quality', weight: 20, desc: 'Explicit confirmations, not assumptions.', color: 'bg-harbor' },
  { label: 'Temporal Validity', weight: 15, desc: 'Freshness of scores, budgets, deadlines.', color: 'bg-harbor' },
]

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
      {/* Hero */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-[10%] w-72 h-72 bg-mist/60 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-mist/40 rounded-full blur-3xl animate-float-slow" />
        </div>
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <span className="inline-flex items-center gap-2 bg-cloud text-ink rounded-full px-5 py-2 text-sm font-medium mb-8">
              <Brain size={14} /> AI Engine
            </span>
          </ScrollReveal>
          <ScrollReveal delay={200} variant="scale-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-[1.1] mb-6 tracking-tight font-heading">
              Intelligence you{' '}<span className="text-harbor">can trust</span>
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              The engine behind every match, every recommendation, every insight. Transparent by design — every output shows its reasoning.
            </p>
          </ScrollReveal>
          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-harbor hover:bg-harbor-hover text-white" asChild>
                <Link to="/signup">Get Started Free <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
                <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* How it works — pipeline */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">How the engine works</h2>
              <p className="text-muted-foreground max-w-xl mx-auto text-lg">Seven stages turn conversation into explainable recommendations.</p>
            </div>
          </ScrollReveal>

          <div className="flex flex-wrap justify-center items-start gap-3 lg:gap-0">
            {pipelineSteps.map((step, i) => (
              <ScrollReveal key={i} delay={i * 60} variant="fade-up">
                <div className="flex items-center">
                  <div className="w-32 sm:w-36 flex flex-col items-center text-center">
                    <div className="w-14 h-14 rounded-xl bg-harbor text-white flex items-center justify-center mb-2 shadow-md">
                      <step.icon size={22} />
                    </div>
                    <h3 className="text-xs font-bold text-foreground mb-0.5 font-heading">{step.title}</h3>
                    <p className="text-[11px] text-muted-foreground leading-snug px-1">{step.desc}</p>
                  </div>
                  {i < pipelineSteps.length - 1 && (
                    <div className="hidden lg:flex items-center px-0.5 mt-[-2rem]">
                      <ChevronRight size={16} className="text-gray-300" />
                    </div>
                  )}
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Confidence scoring */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">Confidence you can see</h2>
              <p className="text-muted-foreground max-w-xl mx-auto text-lg">A four-dimension scoring model you can inspect, understand, and improve.</p>
            </div>
          </ScrollReveal>

          <div className="grid sm:grid-cols-2 gap-5">
            {confidenceDimensions.map((dim, i) => (
              <ScrollReveal key={i} delay={i * 80} variant="fade-up">
                <div className="bg-card rounded-xl border p-5">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-bold text-foreground font-heading">{dim.label}</h3>
                    <span className="text-sm font-bold text-harbor"><AnimatedCounter end={dim.weight} suffix="%" /></span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full mb-2 overflow-hidden">
                    <div className={`h-full rounded-full ${dim.color}`} style={{ width: `${dim.weight}%` }} />
                  </div>
                  <p className="text-xs text-muted-foreground">{dim.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal delay={400}>
            <div className="mt-10 bg-cloud rounded-xl border border-gray-200 p-6 text-center">
              <p className="text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">0-39</span> Insufficient — focused follow-ups{' · '}
                <span className="font-semibold text-foreground">40-69</span> Provisional — limited shortlist with warnings{' · '}
                <span className="font-semibold text-foreground">70-84</span> Ready — full shortlist with fit rationale{' · '}
                <span className="font-semibold text-foreground">85-100</span> High confidence — detailed tradeoff analysis
              </p>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Trust */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-2xl sm:text-3xl font-bold text-center text-foreground mb-10 font-heading">Built on trust</h2>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {trustBadges.map((badge, i) => (
                <div key={i} className="bg-card rounded-xl border p-4 flex flex-col items-center text-center hover:shadow-md transition-shadow">
                  <badge.icon size={22} className="text-harbor mb-2" />
                  <span className="text-xs font-bold text-foreground">{badge.label}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-ink to-ink">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 font-heading">See the engine in action</h2>
            <p className="text-gray-300 mb-10 text-lg max-w-xl mx-auto">Whether you're a student exploring programs or an institution optimizing admissions — the engine works for you.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-harbor hover:bg-harbor-hover text-white" asChild>
                <Link to="/signup">Get Started Free <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg border-harbor text-white hover:bg-ink hover:text-white" asChild>
                <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
