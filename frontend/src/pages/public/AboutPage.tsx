import { Link } from 'react-router-dom'
import { Compass, Eye, Handshake, Lightbulb, Scale, ShieldCheck, UserCheck } from 'lucide-react'

import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'

// Spec 07 (Product Context §1/§2/§3/§5/§6) — positioning + the four operative
// brand values + the AI-trust commitments the market told us it cares about.

const VALUES = [
  {
    icon: Compass,
    title: 'Fit, not fame',
    body: 'We optimize for where you’ll actually thrive — not for brand rank. Big-name programs shouldn’t be a blockade to everyone else.',
  },
  {
    icon: Lightbulb,
    title: 'Explain everything',
    body: 'Every score, rank, and recommendation arrives with its reasoning. No black boxes.',
  },
  {
    icon: Handshake,
    title: 'Partnership, not extraction',
    body: 'We sell software, not students. Your raw data is never sold; sharing is permissioned and de-identified.',
  },
  {
    icon: Scale,
    title: 'Bias-avoidance is a practice',
    body: 'Cohorts are audited for disparate impact, and consequential decisions always keep a human in the loop.',
  },
]

const PRINCIPLES = [
  { icon: Eye, title: 'Transparent', body: 'You can see why the system suggests what it does.' },
  { icon: UserCheck, title: 'Human-final', body: 'AI drafts and suggests; people decide.' },
  { icon: ShieldCheck, title: 'Private by design', body: 'Your data works for you, under your consent.' },
]

export default function AboutPage() {
  usePageTitle('About')
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-12 sm:py-16">
      {/* Hero */}
      <header className="max-w-2xl">
        <p className="text-eyebrow uppercase tracking-[0.22em] text-cobalt font-semibold">
          About UniPaith
        </p>
        <h1 className="text-h1 sm:text-display text-charcoal mt-3">
          The two-sided, AI-supported admissions layer.
        </h1>
        <p className="mt-5 text-lg text-slate">
          Students get a portable profile, program matching, and decision support. Institutions get
          marketing, review, and insight. One shared, explainable network — so you can apply once and
          go anywhere.
        </p>
      </header>

      {/* Why we exist */}
      <section className="mt-12">
        <h2 className="text-h2 text-charcoal">Why we exist</h2>
        <p className="mt-3 text-slate">
          Traditional big schools and programs form a blockade for everyone else to reach. We give
          smaller and regional programs reach, and give students real options beyond the prestige
          monopoly. We start where the pain is highest — community colleges and regional public
          institutions — and grow from there. This is a beachhead, not a ceiling.
        </p>
      </section>

      {/* Values */}
      <section className="mt-12">
        <h2 className="text-h2 text-charcoal">What we stand for</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {VALUES.map(v => (
            <Card key={v.title} className="p-5">
              <v.icon size={20} className="text-cobalt" />
              <h3 className="text-h3 text-charcoal mt-3">{v.title}</h3>
              <p className="mt-1.5 text-sm text-slate">{v.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* AI principles */}
      <section className="mt-12">
        <h2 className="text-h2 text-charcoal">How we use AI</h2>
        <p className="mt-3 text-slate">
          The market told us what matters: transparency, a human final decision, and privacy. We
          built for exactly that.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {PRINCIPLES.map(p => (
            <div key={p.title} className="rounded-lg border border-border bg-card p-5">
              <p.icon size={18} className="text-cobalt" />
              <h3 className="font-semibold text-charcoal mt-2">{p.title}</h3>
              <p className="mt-1 text-sm text-slate">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Closing CTA */}
      <section className="mt-14 rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-h3 text-charcoal">Your path, simplified.</p>
        <p className="mt-2 text-slate">Apply once, go anywhere.</p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/signup">
            <Button size="lg">Get started</Button>
          </Link>
          <Link to="/pricing">
            <Button size="lg" variant="tertiary">
              See pricing
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
