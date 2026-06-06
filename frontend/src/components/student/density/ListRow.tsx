// Density layer — a dense list row: optional left media, a title + dense subline,
// and a trailing slot. Hairline divider + hover when interactive (no bordered
// "pill" box), so ~50% more rows fit per screen than the current pill lists.

interface ListRowProps {
  media?: React.ReactNode
  title: React.ReactNode
  sub?: React.ReactNode
  trailing?: React.ReactNode
  onClick?: () => void
}

export default function ListRow({ media, title, sub, trailing, onClick }: ListRowProps) {
  const inner = (
    <>
      {media && <span className="shrink-0">{media}</span>}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-foreground">{title}</span>
        {sub && <span className="block truncate text-xs text-muted-foreground">{sub}</span>}
      </span>
      {trailing && <span className="shrink-0">{trailing}</span>}
    </>
  )
  const base = 'flex w-full items-center gap-3 border-b border-border py-2 text-left last:border-0'
  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`${base} -mx-2 rounded-md px-2 transition-colors hover:bg-muted/50`}
      >
        {inner}
      </button>
    )
  }
  return <div className={base}>{inner}</div>
}
