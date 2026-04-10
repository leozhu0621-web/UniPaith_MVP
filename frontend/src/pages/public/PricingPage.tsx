import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/shadcn/accordion'
import { ArrowRight, Check, GraduationCap, Building2 } from 'lucide-react'

const studentFeatures = [
  'Universal Profile',
  'AI-powered matching',
  'Application tracker',
  'Essay workshop',
  'Financial aid navigator',
  'AI counselor 24/7',
  'Readiness diagnostics',
  'Document management',
]

const institutionFeatures = [
  'Pipeline board & review queue',
  'AI triage & score suggestions',
  'Unified messaging hub',
  'Segments & campaign tools',
  'Analytics dashboard',
  'Events management',
  'Data upload & migration',
  'FERPA/GDPR compliance built-in',
]

const faqs = [
  { q: 'Is there really no cost for students?', a: 'Correct. Students never pay — no trial, no premium tier, no credit card. We\'re funded by institutional partnerships.' },
  { q: 'How does institution pricing work?', a: 'Usage-based pricing tied to pipeline volume. No multi-year contracts. Start with a pilot, scale when you see results.' },
  { q: 'Is there a free tier for institutions?', a: 'Yes. Community colleges and eligible regional institutions can access a free entry tier. Contact us for details.' },
  { q: 'Can we try before we commit?', a: 'Absolutely. We offer a no-commitment pilot so you can see results before scaling.' },
]

export default function PricingPage() {
  return (
    <div className="pt-16">
      {/* Hero */}
      <section className="py-24 sm:py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground mb-6 tracking-tight font-heading">
              Simple, transparent pricing
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Free for students, always. Flexible plans for institutions.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* Pricing cards */}
      <section className="pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          {/* Student card */}
          <ScrollReveal delay={100} variant="fade-left">
            <div className="bg-card rounded-2xl border-2 border-brand-amber-200 p-8 sm:p-10 h-full flex flex-col">
              <div className="w-14 h-14 rounded-xl bg-brand-amber-100 flex items-center justify-center mb-5">
                <GraduationCap className="text-brand-amber-600" size={28} />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2 font-heading">Students</h2>
              <div className="mb-4">
                <span className="text-4xl font-bold text-foreground font-heading">Free</span>
                <span className="text-muted-foreground ml-2">forever</span>
              </div>
              <p className="text-muted-foreground text-sm mb-6">Everything you need to find, match, apply, and track — at no cost.</p>

              <ul className="space-y-3 mb-8 flex-1">
                {studentFeatures.map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-foreground">
                    <Check size={16} className="text-brand-green-500 flex-shrink-0" /> {f}
                  </li>
                ))}
              </ul>

              <Button size="lg" className="w-full rounded-xl py-6 text-base bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
                <Link to="/signup?role=student">Create Your Profile <ArrowRight size={18} className="ml-2" /></Link>
              </Button>
            </div>
          </ScrollReveal>

          {/* Institution card */}
          <ScrollReveal delay={200} variant="fade-right">
            <div className="bg-card rounded-2xl border-2 border-brand-slate-200 p-8 sm:p-10 h-full flex flex-col">
              <div className="w-14 h-14 rounded-xl bg-brand-slate-100 flex items-center justify-center mb-5">
                <Building2 className="text-brand-slate-600" size={28} />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2 font-heading">Institutions</h2>
              <div className="mb-4">
                <span className="text-4xl font-bold text-foreground font-heading">Custom</span>
                <span className="text-muted-foreground ml-2">per volume</span>
              </div>
              <p className="text-muted-foreground text-sm mb-6">Usage-based pricing. No multi-year contracts. Start with a pilot.</p>

              <ul className="space-y-3 mb-8 flex-1">
                {institutionFeatures.map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-foreground">
                    <Check size={16} className="text-brand-slate-600 flex-shrink-0" /> {f}
                  </li>
                ))}
              </ul>

              <Button size="lg" variant="outline" className="w-full rounded-xl py-6 text-base border-brand-slate-600 text-brand-slate-600 hover:bg-brand-slate-600 hover:text-white" asChild>
                <Link to="/signup?role=institution_admin">Schedule a Demo <ArrowRight size={18} className="ml-2" /></Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-center text-foreground mb-10 font-heading">Pricing FAQ</h2>
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
    </div>
  )
}
