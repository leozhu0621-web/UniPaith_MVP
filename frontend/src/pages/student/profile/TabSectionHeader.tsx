/**
 * Dense section header for the merged Academics & experience tab
 * (Profile refinement v2, 2026-06-18). Smaller and tighter than the
 * profile/shared `SectionHeader` (which renders an oversized `text-h3`): a
 * compact `text-sm font-semibold` label with the Add action right-aligned and a
 * bottom rule, so the merged tab reads as a dense, app-like record instead of a
 * stack of big headings. Scoped to these two tabs — the shared header stays for
 * Preferences / Costs & aid / Documents / Interviews, which don't merge.
 */
interface TabSectionHeaderProps {
  title: string
  action?: React.ReactNode
}

export function TabSectionHeader({ title, action }: TabSectionHeaderProps) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3 border-b border-border pb-2">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
