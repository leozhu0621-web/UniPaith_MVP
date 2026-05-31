import { Link } from 'react-router-dom'
import { useBilling } from '../../hooks/useBilling'

// A single, restrained house-ad slot (Spec 06 §4.1 — "ad revenue from
// non-upgraders"). Doubles as the $5/mo ad-free upsell. Shown only to
// non-ad-free subscribers and free-tier users; never during the full-access
// trial, and never when billing is disabled. Deliberately quiet — no images,
// no gradients (brand: yellow is punctuation, not fill).
export default function AdSlot({ className = '' }: { className?: string }) {
  const { data } = useBilling()
  const show = Boolean(data?.enabled) && !data?.ad_free && data?.plan !== 'trial'
  if (!show) return null

  return (
    <div
      className={`rounded-lg border border-dashed border-border bg-muted/30 px-4 py-3 ${className}`}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
            Sponsored
          </p>
          <p className="text-sm text-charcoal mt-0.5">
            Tired of ads? Go ad-free for $5/month.
          </p>
        </div>
        <Link
          to="/s/billing"
          className="text-xs font-semibold text-cobalt hover:underline whitespace-nowrap"
        >
          Remove ads
        </Link>
      </div>
    </div>
  )
}
