// Density layer — a compact section label (eyebrow + count). The standard way to
// title a sub-section across student surfaces. See docs/superpowers/specs/
// 2026-06-04-student-ux-densification-design.md.

interface SectionHeaderProps {
  children: React.ReactNode
  count?: number
  action?: React.ReactNode
  className?: string
}

export default function SectionHeader({ children, count, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between gap-2 mb-2 ${className}`}>
      <h2 className="text-eyebrow uppercase text-muted-foreground">
        {children}
        {count != null && <span className="ml-1.5 text-muted-foreground/70">{count}</span>}
      </h2>
      {action}
    </div>
  )
}
