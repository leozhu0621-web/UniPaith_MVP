import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import {
  ArrowRight, MessageCircle, UserCircle, Search, Send, Target,
  FileText, DollarSign, Shield, Sparkles, Lock, BookOpen, Brain,
} from 'lucide-react'

const journeyStages = [
  { num: '01', title: 'Tell Us About You', desc: 'Goals, budget, location, timeline — a quick conversation, not a 20-page form.', color: 'bg-harbor' },
  { num: '02', title: 'Spot the Blind Spots', desc: 'We flag things you might miss: visa requirements, hidden costs, eligibility gaps.', color: 'bg-ink' },
  { num: '03', title: 'Lock In Your Priorities', desc: 'Cost vs ranking, location vs timeline — you decide the tradeoffs, we respect them.', color: 'bg-harbor' },
  { num: '04', title: 'Build Your Shortlist', desc: 'Programs matched to your criteria. You\'ll see why each one made the cut.', color: 'bg-ink' },
  { num: '05', title: 'Get Application-Ready', desc: 'Checklists, documents, essays — everything organized with clear next steps.', color: 'bg-harbor' },
  { num: '06', title: 'Apply From One Dashboard', desc: 'Submit to multiple programs without re-entering the same info on 12 portals.', color: 'bg-ink' },
  { num: '07', title: 'Track Every Response', desc: 'Status updates, interview invites, and decisions — all in one feed.', color: 'bg-harbor' },
  { num: '08', title: 'Compare Offers & Decide', desc: 'Side-by-side comparison with real costs, conditions, and deadlines.', color: 'bg-ink' },
]

const features = [
  { icon: UserCircle, title: 'One Profile, Every School', desc: 'Fill it out once. Academics, activities, essays, documents — reuse across every application.', color: 'text-harbor', bg: 'bg-mist' },
  { icon: Search, title: 'Smart Matching', desc: 'Programs ranked by how well they fit your goals, budget, and profile — with clear reasoning.', color: 'text-harbor', bg: 'bg-mist' },
  { icon: Send, title: 'Application Tracker', desc: 'Deadlines, checklists, status — stop juggling spreadsheets and email tabs.', color: 'text-ink', bg: 'bg-ink/10' },
  { icon: FileText, title: 'Essay Workshop', desc: 'Get feedback on your essays, track versions, and tailor drafts per program.', color: 'text-ink', bg: 'bg-ink/10' },
  { icon: DollarSign, title: 'Cost & Aid Breakdown', desc: 'Compare real costs across programs. Find scholarships you qualify for.', color: 'text-harbor', bg: 'bg-mist' },
  { icon: Target, title: 'Readiness Check', desc: 'Know where you stand before you hit submit. Strengths, gaps, and what to fix.', color: 'text-harbor', bg: 'bg-mist' },
]

const chatMessages = [
  { from: 'ai', text: "Your top priorities: budget under $30K/year, strong CS program, North America. Still right?" },
  { from: 'student', text: "Yes, but I'm now open to Europe if it's cheaper." },
  { from: 'ai', text: "Good call. 3 programs in Germany and 2 in the Netherlands have zero tuition for international students. Want me to add them to your shortlist?" },
]

const faqs = [
  { q: 'How is this different from Common App?', a: 'Common App handles submission to ~1,100 member schools. UniPaith handles matching, readiness, applications, tracking, and offer comparison — across any program worldwide. One profile works everywhere.' },
  { q: 'Is it really free?', a: 'Yes. Institutions pay for their operations platform. Students pay nothing — no trial, no premium tier, no credit card.' },
  { q: 'Does the AI decide where I apply?', a: 'No. It recommends programs and shows you why. You choose where to apply, what to submit, and which offer to accept.' },
  { q: 'What happens to my data?', a: 'It\'s yours. Encrypted, never sold, only shared with schools you choose to apply to. Export or delete anytime.' },
]

export default function ForStudentsPage() {
  return (
    <div className="pt-16">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 lg:px-8 overflow-hidden bg-cloud">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-[10%] w-72 h-72 bg-mist rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-sand-light/40 rounded-full blur-3xl animate-float-slow" />
        </div>
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <span className="inline-flex items-center gap-2 bg-mist text-harbor rounded-full px-5 py-2 text-sm font-medium mb-8">
              Everything a $6K agent does &mdash; for free
            </span>
          </ScrollReveal>
          <ScrollReveal delay={200} variant="scale-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-ink leading-[1.1] mb-6 tracking-tight font-heading">
              Find the right school.{' '}
              <br className="hidden sm:block" />
              <span className="text-harbor">Get in.</span>
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={400}>
            <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
              UniPaith matches you with programs that actually fit, manages your applications, and helps you put your best foot forward &mdash; all from one place.
            </p>
          </ScrollReveal>
          <ScrollReveal delay={600}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-harbor hover:bg-harbor-hover text-white" asChild>
                <Link to="/signup?role=student">Create Your Profile <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg border-gray-300 text-ink hover:bg-mist" asChild>
                <a href="#how-it-works">See How It Works</a>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-3 font-heading">Here&rsquo;s what happens when you sign up</h2>
              <p className="text-gray-500 max-w-lg mx-auto text-lg">Eight steps. One place. No guesswork.</p>
            </div>
          </ScrollReveal>
          <div className="relative">
            <div className="hidden md:block absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-6">
              {journeyStages.map((stage, i) => (
                <ScrollReveal key={i} delay={i * 80} variant="fade-left">
                  <div className="flex gap-6 items-start">
                    <div className={`flex-shrink-0 w-14 h-14 rounded-xl ${stage.color} text-white flex items-center justify-center font-bold text-base font-heading z-10`}>
                      {stage.num}
                    </div>
                    <div className="flex-1 bg-cloud rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow">
                      <h3 className="text-base font-bold text-ink mb-0.5 font-heading">{stage.title}</h3>
                      <p className="text-gray-500 text-sm">{stage.desc}</p>
                    </div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* What you get */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-cloud">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-3 font-heading">What you get</h2>
              <p className="text-gray-500 max-w-lg mx-auto text-lg">Six tools that work together so you don&rsquo;t have to juggle six apps.</p>
            </div>
          </ScrollReveal>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <ScrollReveal key={i} delay={i * 80} variant="fade-up">
                <div className="bg-white rounded-2xl border border-gray-200 p-7 hover:shadow-md transition-all h-full group">
                  <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                    <f.icon className={`${f.color} transition-transform duration-300 group-hover:scale-110`} size={24} />
                  </div>
                  <h3 className="text-lg font-bold text-ink mb-2 font-heading">{f.title}</h3>
                  <p className="text-gray-500 text-sm">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Counselor preview */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-ink">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="text-center mb-14">
              <span className="inline-flex items-center gap-1.5 bg-harbor/20 text-harbor text-sm font-medium rounded-full px-5 py-1.5 mb-4">
                <MessageCircle size={14} /> Your Counselor
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 font-heading">Like texting a friend who knows admissions inside out</h2>
              <p className="text-gray-400 max-w-xl mx-auto text-lg">Ask anything. It knows your profile, your priorities, and your deadlines.</p>
            </div>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="max-w-2xl mx-auto bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
              <div className="px-6 py-3 border-b border-white/10 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-harbor flex items-center justify-center"><Sparkles size={16} className="text-white" /></div>
                <span className="text-white font-medium text-sm">UniPaith</span>
              </div>
              <div className="p-5 space-y-3">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.from === 'student' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.from === 'student' ? 'bg-harbor text-white rounded-br-sm' : 'bg-white/10 text-gray-200 rounded-bl-sm'
                    }`}>{msg.text}</div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Trust */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-cloud">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-3 font-heading">You stay in control</h2>
            <p className="text-gray-500 max-w-xl mx-auto text-lg mb-10">Every recommendation shows its reasoning. You can edit, reject, or override anything.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { icon: Shield, label: 'FERPA & GDPR' },
                { icon: Lock, label: 'Encrypted' },
                { icon: Brain, label: 'You Decide' },
                { icon: BookOpen, label: 'Full Audit Trail' },
              ].map((badge, i) => (
                <div key={i} className="flex flex-col items-center gap-2 p-4">
                  <badge.icon size={24} className="text-harbor" />
                  <span className="text-sm font-medium text-ink">{badge.label}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-center text-ink mb-10 font-heading">Common questions</h2>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <Accordion type="single" collapsible className="space-y-3">
              {faqs.map((faq, i) => (
                <AccordionItem key={i} value={`faq-${i}`} className="bg-cloud rounded-xl border border-gray-200 px-6">
                  <AccordionTrigger className="text-left font-semibold text-ink hover:no-underline py-4 text-sm">{faq.q}</AccordionTrigger>
                  <AccordionContent className="text-gray-500 text-sm pb-4">{faq.a}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </ScrollReveal>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-ink">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 font-heading">Ready to get started?</h2>
            <p className="text-gray-400 mb-10 text-lg max-w-xl mx-auto">Set up your profile in under 2 minutes. No cost, no commitment.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <Button size="lg" className="text-base px-12 py-7 rounded-xl shadow-lg text-lg bg-harbor hover:bg-harbor-hover text-white" asChild>
              <Link to="/signup?role=student">Create Your Profile <ArrowRight size={20} className="ml-2" /></Link>
            </Button>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
