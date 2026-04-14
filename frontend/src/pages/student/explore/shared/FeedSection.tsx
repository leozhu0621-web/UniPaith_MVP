import { ChevronRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Props {
  icon: LucideIcon
  title: string
  count?: number
  onSeeAll?: () => void
  children: React.ReactNode
}

export default function FeedSection({ icon: Icon, title, count, onSeeAll, children }: Props) {
  return (
    <section className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-student-ink flex items-center gap-2">
          <Icon size={16} className="text-student" /> {title}
          {count != null && <span className="text-xs font-normal text-student-text">({count})</span>}
        </h2>
        {onSeeAll && (
          <button onClick={onSeeAll} className="text-xs text-student font-medium flex items-center gap-0.5 hover:underline">
            See all <ChevronRight size={12} />
          </button>
        )}
      </div>
      {children}
    </section>
  )
}
