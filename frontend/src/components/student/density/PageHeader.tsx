// Density layer — a compact page header (eyebrow + small heading + inline count +
// optional sub + right-aligned actions). Replaces magazine-scale per-page headings
// with an app-scale one, applied across all student surfaces.

interface PageHeaderProps {
  eyebrow?: string
  title: string
  count?: number
  sub?: string
  actions?: React.ReactNode
}

export default function PageHeader({ eyebrow, title, count, sub, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 mb-3">
      <div className="min-w-0">
        {eyebrow && <p className="text-eyebrow uppercase text-secondary mb-0.5">{eyebrow}</p>}
        <h1 className="text-lg font-semibold leading-tight text-foreground">
          {title}
          {count != null && <span className="ml-2 text-sm font-normal text-muted-foreground">{count}</span>}
        </h1>
        {sub && <p className="mt-0.5 text-[13px] text-muted-foreground">{sub}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
