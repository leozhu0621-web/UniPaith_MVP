// Density layer — a compact page header (eyebrow + small heading + inline count +
// optional sub + right-aligned actions). Replaces magazine-scale per-page headings
// with an app-scale one, applied across all student surfaces.

// No subtitle line — page headers are title + optional eyebrow/count only.
// (Founder direction 2026-06-14: "I don't want the small comment around the
// title anywhere in this product." The descriptive `sub` tagline is removed
// app-wide; tsc flags any call site still passing it.)
interface PageHeaderProps {
  eyebrow?: string
  title: string
  count?: number
  actions?: React.ReactNode
}

export default function PageHeader({ eyebrow, title, count, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 mb-3">
      <div className="min-w-0">
        {eyebrow && <p className="text-eyebrow uppercase text-secondary mb-0.5">{eyebrow}</p>}
        <h1 className="text-lg font-semibold leading-tight text-foreground">
          {title}
          {count != null && <span className="ml-2 text-sm font-normal text-muted-foreground">{count}</span>}
        </h1>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
