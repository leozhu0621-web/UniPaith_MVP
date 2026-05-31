import { Link } from 'react-router-dom'
import { Building2, Check, GraduationCap, Minus, Sparkles } from 'lucide-react'

import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'

// Spec 07 (Product Context §1/§2/§4) — public pricing surface. Static by design:
// the billing engine + entitlements live behind auth (Spec 06 §4). These figures
// mirror the backend billing defaults — $15/mo "UniPaith Plus", +$5/mo ad-free,
// 7-day trial, $15 / unique applicant — and the free-vs-Plus matrix mirrors the
// entitlement map, so this page stays consistent with the live billing.

const PLUS_PRICE = 15
const ADFREE_PRICE = 5
const INSTITUTION_PRICE = 15
const TRIAL_DAYS = 7

const PLUS_FEATURES = [
  'Full ranked matching with reasoning',
  'Real-time deadline alerts',
  'Scholarship and affordability tools',
  'Essay, resume, and interview workshops',
]

const INSTITUTION_FEATURES = [
  'Reach the students who fit your programs',
  'Explainable review and cohort insight',
  'Outreach, events, and posts in one place',
  'Attribution from impression to enrollment',
]

const MATRIX = [
  { label: 'Portable universal profile', free: true, plus: true },
  { label: 'Baseline readiness check', free: true, plus: true },
  { label: 'Program matching (shortlist)', free: true, plus: true },
  { label: 'Full ranked matching + reasoning', free: false, plus: true },
  { label: 'Real-time deadline alerts', free: false, plus: true },
  { label: 'Scholarship and affordability tools', free: false, plus: true },
  { label: 'Essay, resume, and interview workshops', free: false, plus: true },
]

const VALUES = [
  { title: 'Fit, not fame', body: 'Matching optimizes where you’ll thrive, not brand rank.' },
  { title: 'Explain everything', body: 'Every score and recommendation ships with its reasoning.' },
  { title: 'Partnership, not extraction', body: 'We sell software, never your raw data.' },
  { title: 'Bias-avoidance is a practice', body: 'Cohorts are audited and decisions stay human.' },
]

const FAQ = [
  {
    q: 'Is there a free plan?',
    a: 'Yes. Your portable profile, a baseline readiness check, and limited matching are always free. Plus unlocks full matching, deadline alerts, affordability tools, and workshops.',
  },
  {
    q: 'What happens after the 7-day trial?',
    a: 'You get full Plus access for 7 days. After that it’s $15/month — cancel any time before renewal and you keep the free plan.',
  },
  {
    q: 'How does institution pricing work?',
    a: 'Institutions pay $15 per unique applicant processed — usage-based, with no per-seat fees.',
  },
  {
    q: 'Do you sell my data?',
    a: 'No. Partnership, not extraction: we never sell raw student data. De-identified, permissioned signals improve matching only under your explicit consent.',
  },
]

export default function PricingPage() {
  usePageTitle('Pricing')
  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-12 sm:py-16">
      {/* Hero */}
      <header className="text-center max-w-2xl mx-auto">
        <p className="text-eyebrow uppercase tracking-[0.22em] text-cobalt font-semibold">Pricing</p>
        <h1 className="text-h1 sm:text-display text-charcoal mt-3">Simple pricing for your whole journey</h1>
        <p className="mt-4 text-lg text-slate">
          Everyone’s private college counselor — apply once, go anywhere. Start free, upgrade when
          you’re ready.
        </p>
      </header>

      {/* Plans */}
      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <Card variant="card-accent" className="p-7 flex flex-col">
          <div className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-sm font-semibold text-charcoal">
              <GraduationCap size={18} className="text-cobalt" /> For students
            </span>
            <Badge variant="warning">
              <Sparkles size={12} /> {TRIAL_DAYS}-day free trial
            </Badge>
          </div>
          <h2 className="text-h2 text-charcoal mt-4">UniPaith Plus</h2>
          <p className="mt-1 text-slate">Everyone’s private college counselor.</p>
          <div className="mt-5 flex items-baseline gap-1.5">
            <span className="text-h1 text-charcoal leading-none">${PLUS_PRICE}</span>
            <span className="text-slate">/month</span>
          </div>
          <p className="mt-1 text-sm text-slate">
            {TRIAL_DAYS}-day free trial, then ${PLUS_PRICE}/month. Cancel any time. Optional +$
            {ADFREE_PRICE}/mo ad-free.
          </p>
          <ul className="mt-5 space-y-2 flex-1">
            {PLUS_FEATURES.map(f => (
              <li key={f} className="flex items-start gap-2 text-sm text-charcoal">
                <Check size={16} className="text-success mt-0.5 shrink-0" /> {f}
              </li>
            ))}
          </ul>
          <Link to="/signup" className="mt-6 block">
            <Button className="w-full">Start your {TRIAL_DAYS}-day trial</Button>
          </Link>
        </Card>

        <Card className="p-7 flex flex-col">
          <span className="flex items-center gap-2 text-sm font-semibold text-charcoal">
            <Building2 size={18} className="text-cobalt" /> For institutions
          </span>
          <h2 className="text-h2 text-charcoal mt-4">Institution</h2>
          <p className="mt-1 text-slate">The admission operating system.</p>
          <div className="mt-5 flex items-baseline gap-1.5">
            <span className="text-h1 text-charcoal leading-none">${INSTITUTION_PRICE}</span>
            <span className="text-slate">/ applicant processed</span>
          </div>
          <p className="mt-1 text-sm text-slate">Usage-based. No per-seat fees, no lock-in.</p>
          <ul className="mt-5 space-y-2 flex-1">
            {INSTITUTION_FEATURES.map(f => (
              <li key={f} className="flex items-start gap-2 text-sm text-charcoal">
                <Check size={16} className="text-success mt-0.5 shrink-0" /> {f}
              </li>
            ))}
          </ul>
          <Link to="/signup" className="mt-6 block">
            <Button variant="secondary" className="w-full">
              Get started
            </Button>
          </Link>
        </Card>
      </div>

      {/* Free vs Plus */}
      <section className="mt-16">
        <h2 className="text-h2 text-charcoal text-center">Free vs Plus</h2>
        <div className="mt-6 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-card border-b border-border text-left">
                <th className="px-4 py-3 font-semibold text-charcoal">Feature</th>
                <th className="px-4 py-3 font-semibold text-charcoal text-center w-24">Free</th>
                <th className="px-4 py-3 font-semibold text-charcoal text-center w-24">Plus</th>
              </tr>
            </thead>
            <tbody>
              {MATRIX.map((f, i) => (
                <tr key={f.label} className={i % 2 ? 'bg-muted/30' : ''}>
                  <td className="px-4 py-3 text-charcoal border-t border-border">{f.label}</td>
                  <td className="px-4 py-3 text-center border-t border-border">
                    {f.free ? (
                      <Check size={16} className="text-success inline" />
                    ) : (
                      <Minus size={16} className="text-stone inline" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-center border-t border-border">
                    {f.plus ? (
                      <Check size={16} className="text-success inline" />
                    ) : (
                      <Minus size={16} className="text-stone inline" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Values */}
      <section className="mt-16">
        <h2 className="text-h2 text-charcoal text-center">What we stand for</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {VALUES.map(v => (
            <Card key={v.title} className="p-5">
              <h3 className="text-h3 text-charcoal">{v.title}</h3>
              <p className="mt-1.5 text-sm text-slate">{v.body}</p>
            </Card>
          ))}
        </div>
        <p className="mt-5 text-center text-sm">
          <Link to="/about" className="text-cobalt hover:underline">
            Read more about our approach →
          </Link>
        </p>
      </section>

      {/* FAQ */}
      <section className="mt-16 max-w-2xl mx-auto">
        <h2 className="text-h2 text-charcoal text-center">Questions</h2>
        <dl className="mt-6 divide-y divide-border">
          {FAQ.map(item => (
            <div key={item.q} className="py-4">
              <dt className="font-semibold text-charcoal">{item.q}</dt>
              <dd className="mt-1.5 text-sm text-slate">{item.a}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Closing CTA */}
      <section className="mt-16 text-center">
        <h2 className="text-h2 text-charcoal">Your path, simplified.</h2>
        <p className="mt-2 text-slate">Start your {TRIAL_DAYS}-day free trial — no commitment.</p>
        <Link to="/signup" className="mt-5 inline-block">
          <Button size="lg">Get started</Button>
        </Link>
      </section>
    </div>
  )
}
