import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import {
  ArrowRight, MessageCircle, UserCircle, Search, Send, Target,
  FileText, DollarSign, Shield, Sparkles, Lock, BookOpen, Brain, Heart,
} from 'lucide-react'

const journeyStages = [
  { num: '01', title: 'Understand Your Context', desc: 'Goals, motivations, constraints — through conversation, not forms.', color: 'bg-brand-amber-500' },
  { num: '02', title: 'Surface Hidden Blockers', desc: 'Budget gaps, visa risks, timeline pressure, eligibility unknowns.', color: 'bg-brand-slate-500' },
  { num: '03', title: 'Define Your Priorities', desc: 'Cost vs ranking, location vs timeline — your tradeoffs, your rules.', color: 'bg-brand-amber-500' },
  { num: '04', title: 'Translate to Requirements', desc: 'Goals become must-haves and nice-to-haves. Review and edit anytime.', color: 'bg-brand-slate-500' },
  { num: '05', title: 'Shortlist & Plan', desc: 'Programs with transparent fit rationale. Know why each was picked.', color: 'bg-brand-amber-500' },
  { num: '06', title: 'Prepare & Submit', desc: 'Checklists, documents, essays, deadlines — managed in one place.', color: 'bg-brand-slate-500' },
  { num: '07', title: 'Track & Respond', desc: 'Status updates, interview requests, and decisions as they happen.', color: 'bg-brand-amber-500' },
  { num: '08', title: 'Compare & Decide', desc: 'Side-by-side offers with cost normalization and deadline tracking.', color: 'bg-brand-slate-500' },
]

const features = [
  { icon: UserCircle, title: 'Universal Profile', desc: 'Build once, use everywhere. One portable profile across every application.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: Search, title: 'AI Matching', desc: 'Explainable recommendations tied to your goals, budget, and profile.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
  { icon: Send, title: 'Application Manager', desc: 'Deadlines, checklists, status updates — one dashboard for everything.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: FileText, title: 'Essay Workshop', desc: 'AI-assisted writing with feedback, version history, and program-specific guidance.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
  { icon: DollarSign, title: 'Financial Aid Navigator', desc: 'Discover scholarships, compare costs, and make informed financial decisions.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: Target, title: 'Readiness Diagnostics', desc: 'Know where you stand before you submit. Strengths, gaps, and a clear path.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
]

const chatMessages = [
  { from: 'ai', text: "Based on our conversation, your top priorities are budget under $30K/year and a strong CS program in North America. Still accurate?" },
  { from: 'student', text: "Yes, but I'm also now open to Europe if the cost is lower." },
  { from: 'ai', text: "Adding Europe expands your options — 3 programs in Germany and 2 in the Netherlands have zero tuition for international students. Want me to add them to your shortlist?" },
]

const faqs = [
  { q: 'How is this different from Common App?', a: 'Common App handles submission to ~1,100 member schools. UniPaith handles your entire journey — matching, readiness, applications, tracking, and offer comparison. Your profile works across every institution.' },
  { q: 'Is it really free?', a: 'Yes, completely free — forever. No credit card, no trial period. Institutions pay for their operations platform; students never pay.' },
  { q: 'Does AI decide where I apply?', a: 'Never. AI explains why programs might fit and flags what you\'re missing. Every decision — where to apply, what to submit, which offer to accept — is yours.' },
  { q: 'What happens to my data?', a: 'Your data belongs to you. FERPA-ready, GDPR-compliant, end-to-end encrypted. Export or delete anytime.' },
]

export default function ForStudentsPage() {
  return (
    <div className="pt-16">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-[10%] w-72 h-72 bg-brand-amber-100/60 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-brand-slate-100/40 rounded-full blur-3xl animate-float-slow" />
        </div>
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <span className="inline-flex items-center gap-2 bg-brand-amber-50 text-brand-amber-700 rounded-full px-5 py-2 text-sm font-medium mb-8">
              <Heart size={14} /> For Students
            </span>
          </ScrollReveal>
          <ScrollReveal delay={200} variant="scale-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-[1.1] mb-6 tracking-tight font-heading">
              Your private education advisor.{' '}
              <br className="hidden sm:block" />
              <span className="text-brand-amber-500">Available 24/7.</span>
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              One profile. AI-powered matching. Essay help, deadline tracking, financial guidance — from first thought to final decision. Free forever.
            </p>
          </ScrollReveal>
          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
                <Link to="/signup?role=student">Create Your Profile <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
                <a href="#journey">See How It Works</a>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Journey map */}
      <section id="journey" className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">From first thought to final decision</h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">Eight guided stages. One connected experience.</p>
            </div>
          </ScrollReveal>
          <div className="relative">
            <div className="hidden md:block absolute left-8 top-0 bottom-0 w-0.5 bg-border" />
            <div className="space-y-6">
              {journeyStages.map((stage, i) => (
                <ScrollReveal key={i} delay={i * 80} variant="fade-left">
                  <div className="flex gap-6 items-start">
                    <div className={`flex-shrink-0 w-14 h-14 rounded-xl ${stage.color} text-white flex items-center justify-center font-bold text-base font-heading z-10`}>
                      {stage.num}
                    </div>
                    <div className="flex-1 bg-card rounded-xl border p-5 hover:shadow-sm transition-shadow">
                      <h3 className="text-base font-bold text-foreground mb-0.5 font-heading">{stage.title}</h3>
                      <p className="text-muted-foreground text-sm">{stage.desc}</p>
                    </div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">Everything you need. One place.</h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">Six integrated tools that work together.</p>
            </div>
          </ScrollReveal>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <ScrollReveal key={i} delay={i * 80} variant="fade-up">
                <div className="bg-card rounded-2xl border p-7 hover:shadow-md transition-all h-full group">
                  <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                    <f.icon className={`${f.color} transition-transform duration-300 group-hover:scale-110`} size={24} />
                  </div>
                  <h3 className="text-lg font-bold text-foreground mb-2 font-heading">{f.title}</h3>
                  <p className="text-muted-foreground text-sm">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* AI Counselor */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-slate-900">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <span className="inline-flex items-center gap-1.5 bg-brand-amber-500/20 text-brand-amber-300 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <MessageCircle size={14} /> AI Counselor
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 font-heading">Conversation-first. Not form-first.</h2>
              <p className="text-brand-slate-300 max-w-xl mx-auto text-lg">Your AI counselor learns through dialogue — understanding goals, surfacing blind spots, building requirements you agree with.</p>
            </div>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="max-w-2xl mx-auto bg-brand-slate-800 rounded-2xl border border-brand-slate-700 overflow-hidden">
              <div className="px-6 py-3 border-b border-brand-slate-700 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-brand-amber-500 flex items-center justify-center"><Sparkles size={16} className="text-white" /></div>
                <span className="text-white font-medium text-sm">UniPaith Counselor</span>
              </div>
              <div className="p-5 space-y-3">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.from === 'student' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.from === 'student' ? 'bg-brand-amber-500 text-white rounded-br-sm' : 'bg-brand-slate-700 text-brand-slate-100 rounded-bl-sm'
                    }`}>{msg.text}</div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Trust */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-3 font-heading">You're always in control</h2>
            <p className="text-muted-foreground max-w-xl mx-auto text-lg mb-10">Every recommendation shows its reasoning. Every inference is editable. Every decision is yours.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { icon: Shield, label: 'FERPA & GDPR Ready' },
                { icon: Lock, label: 'End-to-End Encrypted' },
                { icon: Brain, label: 'Human-in-the-Loop' },
                { icon: BookOpen, label: 'Full Audit Trails' },
              ].map((badge, i) => (
                <div key={i} className="flex flex-col items-center gap-2 p-4">
                  <badge.icon size={24} className="text-brand-slate-500" />
                  <span className="text-sm font-medium text-foreground">{badge.label}</span>
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
            <h2 className="text-3xl font-bold text-center text-foreground mb-10 font-heading">Questions students ask</h2>
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
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 font-heading">Ready to take control of your future?</h2>
            <p className="text-brand-slate-300 mb-10 text-lg max-w-xl mx-auto">Create your free profile in under 2 minutes. No credit card, no catches.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <Button size="lg" className="text-base px-12 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup?role=student">Create Your Profile — Free Forever <ArrowRight size={20} className="ml-2" /></Link>
            </Button>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
