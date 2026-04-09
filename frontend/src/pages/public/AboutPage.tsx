import { Link } from 'react-router-dom'
import { Button } from '@/components/shadcn/button'
import ScrollReveal from '@/components/landing/ScrollReveal'
import { ArrowRight, Eye, Heart, Shield, Users } from 'lucide-react'

const founders = [
  {
    name: 'Leo Zhu',
    role: 'Co-Founder · Product & Operations',
    desc: 'International student turned entrepreneur. Navigated the admissions system firsthand — the broken portals, the guesswork, the stress. Built UniPaith to fix it.',
    initials: 'LZ',
    bg: 'bg-brand-amber-100',
    textColor: 'text-brand-amber-700',
  },
  {
    name: 'Rick Arrowood',
    role: 'Co-Founder · Strategy & Partnerships',
    desc: 'Education executive and academic with decades on the institutional side of admissions. Understands the operational challenges admissions teams face daily.',
    initials: 'RA',
    bg: 'bg-brand-slate-100',
    textColor: 'text-brand-slate-700',
  },
]

const values = [
  { icon: Eye, title: 'Transparency', desc: 'Every AI output shows its reasoning. No black boxes, no hidden agendas.' },
  { icon: Heart, title: 'Student-first', desc: 'Free for students, always. Built to serve the people navigating the system.' },
  { icon: Shield, title: 'Human-in-the-loop', desc: 'AI assists, humans decide. Every admissions decision stays with people.' },
  { icon: Users, title: 'Both sides matter', desc: 'Students and institutions are partners, not adversaries. We serve both.' },
]

export default function AboutPage() {
  return (
    <div className="pt-16">
      {/* Hero */}
      <section className="py-24 sm:py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground mb-6 tracking-tight font-heading">
              Built by people who&rsquo;ve{' '}
              <span className="text-primary">lived both sides</span>
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              UniPaith was co-founded by a former international student and an education executive.
              We&rsquo;ve seen the broken parts from every angle — and we&rsquo;re building the fix.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* Mission */}
      <section className="pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <ScrollReveal variant="blur-in">
            <div className="bg-brand-slate-50 rounded-2xl border border-brand-slate-200 p-8 sm:p-10 text-center">
              <h2 className="text-2xl font-bold text-foreground mb-4 font-heading">Our mission</h2>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Make admissions fair, transparent, and efficient for everyone. One connected platform
                where students get AI-powered guidance and institutions get structured, trustworthy data.
                No gatekeepers. No black boxes. No $6K agents guessing on your behalf.
              </p>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Founders */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-center text-foreground mb-12 font-heading">Meet the founders</h2>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 gap-8">
            {founders.map((f, i) => (
              <ScrollReveal key={i} delay={i * 200} variant={i === 0 ? 'fade-left' : 'fade-right'}>
                <div className="bg-card rounded-2xl border p-8 text-center h-full">
                  <div className={`w-16 h-16 rounded-full ${f.bg} flex items-center justify-center mx-auto mb-4`}>
                    <span className={`text-lg font-bold ${f.textColor}`}>{f.initials}</span>
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-1 font-heading">{f.name}</h3>
                  <p className="text-sm text-primary font-medium mb-3">{f.role}</p>
                  <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-center text-foreground mb-12 font-heading">What we believe</h2>
          </ScrollReveal>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((v, i) => (
              <ScrollReveal key={i} delay={i * 100} variant="fade-up">
                <div className="bg-card rounded-2xl border p-6 text-center h-full">
                  <v.icon size={28} className="text-brand-slate-600 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-foreground mb-2 font-heading">{v.title}</h3>
                  <p className="text-muted-foreground text-sm">{v.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-brand-slate-700 to-brand-slate-900">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <h2 className="text-3xl font-bold text-white mb-4 font-heading">Join our mission</h2>
            <p className="text-brand-slate-300 mb-8 text-lg">Whether you're a student or an institution — we're building this for you.</p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
                <Link to="/signup">Get Started <ArrowRight size={20} className="ml-2" /></Link>
              </Button>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
