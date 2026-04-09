import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import AnimatedCounter from '@/components/landing/AnimatedCounter'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import {
  ArrowRight, MessageCircle, UserCircle, Search, Send, Target,
  FileText, DollarSign, Shield, CheckCircle2, Sparkles, Clock,
  BookOpen, Heart, Brain, Lock, ChevronRight,
} from 'lucide-react'

/* ── Journey stages from UX flow map ── */
const journeyStages = [
  { num: '01', title: 'Understand Your Context', desc: 'Tell your story — goals, motivations, constraints. The AI builds a baseline from natural conversation, not forms.', color: 'bg-brand-amber-500' },
  { num: '02', title: 'Identify Hidden Blockers', desc: 'Surface issues you might not see yet: budget gaps, visa risks, timeline pressure, eligibility unknowns.', color: 'bg-brand-slate-500' },
  { num: '03', title: 'Define Your Priorities', desc: 'Clarify tradeoffs — cost vs ranking, location vs timeline. Your priorities shape every recommendation.', color: 'bg-brand-amber-500' },
  { num: '04', title: 'Translate to Requirements', desc: 'Goals become actionable must-haves and nice-to-haves. Review, edit, confirm — you control the criteria.', color: 'bg-brand-slate-500' },
  { num: '05', title: 'Shortlist & Plan', desc: 'See feasible programs with transparent fit rationale. Know why each was recommended — and what\'s missing.', color: 'bg-brand-amber-500' },
  { num: '06', title: 'Prepare & Submit', desc: 'Checklists, documents, essays, deadlines — managed in one place. Submit when your readiness score says you\'re ready.', color: 'bg-brand-slate-500' },
  { num: '07', title: 'Track & Respond', desc: 'Monitor every application status. Get notified of requests, interviews, and decisions as they happen.', color: 'bg-brand-amber-500' },
  { num: '08', title: 'Compare & Decide', desc: 'Side-by-side offer comparison with cost normalization, conditions, and deadline tracking. Decide with confidence.', color: 'bg-brand-slate-500' },
]

/* ── Feature cards ── */
const features = [
  { icon: UserCircle, title: 'Universal Profile', desc: 'Build once, use everywhere. Academics, activities, essays, documents — one portable profile across every application.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: Search, title: 'AI Matching', desc: 'Explainable recommendations tied to your goals, budget, and profile. See why each program fits — no black boxes.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
  { icon: Send, title: 'Application Manager', desc: 'Track deadlines, manage checklists, monitor status updates. Your entire application portfolio in one dashboard.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: FileText, title: 'Essay Workshop', desc: 'AI-assisted essay writing with feedback, version history, and program-specific guidance. Your voice, sharpened.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
  { icon: DollarSign, title: 'Financial Aid Navigator', desc: 'Understand your budget, discover scholarships, compare costs across programs. Make informed financial decisions.', color: 'text-brand-amber-500', bg: 'bg-brand-amber-50' },
  { icon: Target, title: 'Readiness Diagnostics', desc: 'Know where you stand before you submit. Strengths, gaps, and a clear preparation path — like a GPS for applications.', color: 'text-brand-slate-600', bg: 'bg-brand-slate-50' },
]

/* ── Chat mock messages ── */
const chatMessages = [
  { from: 'ai', text: "Welcome back! Based on our last conversation, I've identified your top priorities as budget under $30K/year and a strong CS program in North America. Does that still feel right?" },
  { from: 'student', text: "Yes, but I'm also now open to Europe if the cost is lower." },
  { from: 'ai', text: "Great update! Adding Europe expands your options significantly. I found 8 more programs that fit your criteria — 3 in Germany and 2 in the Netherlands have zero tuition for international students. Want me to add them to your shortlist?" },
]

/* ── Emotional design urgency model ── */
const urgencyLevels = [
  { label: 'Gentle attention', range: '30+ days', desc: 'Planning language. "Recommended this week."', color: 'bg-brand-slate-100 text-brand-slate-700', dot: 'bg-brand-slate-400' },
  { label: 'Priority window', range: '8–30 days', desc: 'Sequencing language. "Plan for this deadline."', color: 'bg-brand-amber-50 text-brand-amber-700', dot: 'bg-brand-amber-400' },
  { label: 'Focus now', range: '0–7 days', desc: 'Action language — without alarm. "Complete this step today."', color: 'bg-brand-amber-100 text-brand-amber-800', dot: 'bg-brand-amber-600' },
]

/* ── FAQ ── */
const faqs = [
  { q: 'How is this different from Common App?', a: 'Common App handles submission to member schools. UniPaith handles your entire journey — from understanding what you want, to matching with the right programs, to managing applications, tracking decisions, and comparing offers. Plus, your profile works across every institution, not just member schools.' },
  { q: 'Is UniPaith really free for students?', a: 'Yes, completely free — forever. No credit card, no trial period, no premium tier. Students never pay. Institutions pay for the operations platform they use on their side.' },
  { q: 'Does AI decide where I should apply?', a: 'Never. The AI helps you understand your options and explains why programs might be a good fit. Every recommendation comes with transparent reasoning, and you can edit or reject any inference. The final decisions are always yours.' },
  { q: 'What happens to my data?', a: 'Your data belongs to you. We\'re FERPA-ready and GDPR-compliant with end-to-end encryption. You control what institutions can see. You can export or delete your data at any time.' },
  { q: 'Can I still use other application portals?', a: 'Absolutely. UniPaith works alongside other portals, not against them. If a school requires submission through their own system, UniPaith helps you prepare and track — you can use both.' },
  { q: 'What if I\'m not sure what I want to study?', a: 'That\'s exactly when UniPaith is most valuable. The AI counselor starts with open conversation — understanding your goals, interests, and constraints — before translating that into program criteria. It\'s designed for students who are still figuring things out.' },
]

export default function ForStudentsPage() {
  return (
    <div className="pt-16">
      {/* ── Hero ── */}
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
              Your admissions counselor.{' '}
              <br className="hidden sm:block" />
              <span className="text-brand-amber-500">Available 24/7.</span>
            </h1>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              One portable profile. AI-powered matching that explains itself. Essay help, deadline tracking, financial guidance — from first thought to final decision. Free forever.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
                <Link to="/signup?role=student">
                  Create Your Profile
                  <ArrowRight size={20} className="ml-2" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
                <a href="#journey">See How It Works</a>
              </Button>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={800}>
            <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-10 text-sm text-muted-foreground/60">
              <span>Free forever</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>No credit card</span>
              <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
              <span>Your data stays yours</span>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Pain section ── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4 font-heading">
              The admissions process is broken
            </h2>
            <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto text-lg">
              You deserve better than midnight form-filling and guesswork.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-amber-500 font-heading mb-1"><AnimatedCounter end={12} suffix="+" /></div>
                <p className="text-sm text-muted-foreground">applications per student, on average</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-slate-600 font-heading mb-1"><AnimatedCounter end={40} suffix=" hrs" /></div>
                <p className="text-sm text-muted-foreground">spent on repetitive paperwork</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-amber-500 font-heading mb-1"><AnimatedCounter end={68} suffix="%" /></div>
                <p className="text-sm text-muted-foreground">of students feel overwhelmed</p>
              </div>
              <div className="text-center p-6 bg-card rounded-2xl border">
                <div className="text-4xl font-bold text-brand-slate-600 font-heading mb-1">$5K+</div>
                <p className="text-sm text-muted-foreground">spent on agents and intermediaries</p>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-card rounded-2xl border p-8">
                <p className="text-muted-foreground leading-relaxed italic">
                  "It's midnight. You're filling out your eighth application this month. Each one asks for the same transcripts, the same essays, the same scores. You're exhausted — and you're not even sure these schools are right for you."
                </p>
              </div>
              <div className="bg-card rounded-2xl border p-8">
                <p className="text-muted-foreground leading-relaxed italic">
                  "You hired an agent for $3,000. They sent your application to six schools you've never heard of. You have no idea why those were chosen, and they won't explain. You feel like a number, not a person."
                </p>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Journey map ── */}
      <section id="journey" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-block bg-brand-amber-50 text-brand-amber-700 text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
                Your Journey
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                From first thought to final decision
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">
                Eight guided stages. One connected experience. You always know what's next.
              </p>
            </div>
          </ScrollReveal>

          <div className="relative">
            <div className="hidden md:block absolute left-8 top-0 bottom-0 w-0.5 bg-border" />

            <div className="space-y-8">
              {journeyStages.map((stage, i) => (
                <ScrollReveal key={i} delay={i * 100} variant="fade-left">
                  <div className="flex gap-6 md:gap-8 items-start">
                    <div className={`flex-shrink-0 w-16 h-16 rounded-2xl ${stage.color} text-white flex items-center justify-center font-bold text-lg font-heading z-10`}>
                      {stage.num}
                    </div>
                    <div className="flex-1 bg-card rounded-2xl border p-6 hover:shadow-md transition-shadow">
                      <h3 className="text-lg font-bold text-foreground mb-1 font-heading">{stage.title}</h3>
                      <p className="text-muted-foreground text-sm leading-relaxed">{stage.desc}</p>
                    </div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── AI Counselor showcase ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-slate-900">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-flex items-center gap-1.5 bg-brand-amber-500/20 text-brand-amber-300 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <MessageCircle size={14} /> AI Counselor
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 font-heading">
                Conversation-first. Not form-first.
              </h2>
              <p className="text-brand-slate-300 max-w-2xl mx-auto text-lg">
                Your AI counselor learns through natural dialogue — understanding your goals, surfacing blind spots, and building requirements you actually agree with.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="max-w-2xl mx-auto bg-brand-slate-800 rounded-2xl border border-brand-slate-700 overflow-hidden">
              <div className="px-6 py-4 border-b border-brand-slate-700 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-brand-amber-500 flex items-center justify-center">
                  <Sparkles size={16} className="text-white" />
                </div>
                <span className="text-white font-medium text-sm">UniPaith Counselor</span>
                <span className="text-brand-slate-400 text-xs ml-auto">Always available</span>
              </div>

              <div className="p-6 space-y-4">
                {chatMessages.map((msg, i) => (
                  <ScrollReveal key={i} delay={300 + i * 300}>
                    <div className={`flex ${msg.from === 'student' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.from === 'student'
                          ? 'bg-brand-amber-500 text-white rounded-br-sm'
                          : 'bg-brand-slate-700 text-brand-slate-100 rounded-bl-sm'
                      }`}>
                        {msg.text}
                      </div>
                    </div>
                  </ScrollReveal>
                ))}
              </div>

              <div className="px-6 py-4 border-t border-brand-slate-700">
                <div className="flex items-center gap-3 text-brand-slate-400 text-sm">
                  <div className="flex-1 bg-brand-slate-700/50 rounded-xl px-4 py-2.5">Type a message...</div>
                  <div className="w-10 h-10 rounded-xl bg-brand-amber-500 flex items-center justify-center">
                    <ArrowRight size={16} className="text-white" />
                  </div>
                </div>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
              {['Acknowledges your context', 'Guides with concrete actions', 'Explains confidence levels', 'Closes with next steps'].map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-brand-slate-300 text-xs">
                  <CheckCircle2 size={14} className="text-brand-amber-400 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Feature deep-dive ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
                Everything you need. One place.
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto text-lg">
                Six integrated tools that work together — so you don't have to juggle six different apps.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <ScrollReveal key={i} delay={i * 100} variant="fade-up">
                <div className="bg-card rounded-2xl border p-8 hover:shadow-md transition-all h-full group">
                  <div className={`w-14 h-14 rounded-xl ${f.bg} flex items-center justify-center mb-5`}>
                    <f.icon className={`${f.color} transition-transform duration-300 group-hover:scale-110`} size={28} />
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-3 font-heading">{f.title}</h3>
                  <p className="text-muted-foreground leading-relaxed text-sm">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Emotional design / anti-stress ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-16">
              <span className="inline-flex items-center gap-1.5 bg-brand-slate-100 text-brand-slate-700 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <Heart size={14} /> Designed for your wellbeing
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 font-heading">
                An anti-stress admissions experience
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                Applying to schools shouldn't feel like a panic attack. We replaced alarm-heavy urgency with calm, action-oriented guidance.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="space-y-4 mb-12">
              {urgencyLevels.map((level, i) => (
                <div key={i} className={`${level.color} rounded-2xl p-6 flex items-start gap-4`}>
                  <div className={`w-3 h-3 rounded-full ${level.dot} mt-1.5 flex-shrink-0`} />
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-bold text-sm">{level.label}</span>
                      <span className="text-xs opacity-70">({level.range})</span>
                    </div>
                    <p className="text-sm opacity-80">{level.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </ScrollReveal>

          <ScrollReveal delay={400}>
            <div className="grid sm:grid-cols-3 gap-6">
              {[
                { icon: CheckCircle2, title: 'Micro-confirmations', desc: '"Saved." "You\'re still on track." "This update improved your fit."' },
                { icon: ChevronRight, title: 'Next-step anchors', desc: 'One primary action + one optional action. Always clear, never overwhelming.' },
                { icon: Brain, title: 'Uncertainty normalization', desc: '"Here\'s what we don\'t know yet — and here\'s how to resolve it."' },
              ].map((item, i) => (
                <div key={i} className="bg-card rounded-2xl border p-6 text-center">
                  <item.icon className="text-brand-slate-500 mx-auto mb-3" size={24} />
                  <h4 className="font-bold text-foreground text-sm mb-2">{item.title}</h4>
                  <p className="text-muted-foreground text-xs leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ── Trust & transparency ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 font-heading">You're always in control</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg mb-12">
              Every recommendation shows its reasoning. Every AI inference is editable. Every decision is yours.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
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

      {/* ── FAQ ── */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-foreground mb-12 font-heading">
              Questions students ask
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
              Ready to take control of your future?
            </h2>
            <p className="text-brand-slate-300 mb-10 text-lg max-w-xl mx-auto">
              Create your free profile in under 2 minutes. No credit card, no catches, no expiration. Your admissions journey starts here.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <Button size="lg" className="text-base px-12 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup?role=student">
                Create Your Profile — Free Forever
                <ArrowRight size={20} className="ml-2" />
              </Link>
            </Button>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
