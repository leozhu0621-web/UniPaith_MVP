import { Sparkles, ChevronRight } from 'lucide-react'
import type { Promotion } from '../../../../types'

interface Props {
  promo: Promotion
  onView: () => void
}

// Featured/promoted program — gold is the earned "featured" punctuation (eyebrow
// + left accent), but no gradient fill (brand: gold is punctuation, not fill).
export default function PromoCard({ promo, onView }: Props) {
  return (
    <div
      onClick={onView}
      className="bg-card rounded-lg border border-border border-l-2 border-l-student hover:shadow-md transition-shadow overflow-hidden cursor-pointer"
    >
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Sparkles size={12} className="text-primary" />
        <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Featured program</span>
      </div>
      <div className="px-4 pb-4">
        <h3 className="text-sm font-semibold text-foreground mb-1">{promo.title}</h3>
        {promo.description && <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{promo.description}</p>}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">{(promo as { institution_name?: string }).institution_name || ''}</span>
          <span className="text-xs text-secondary font-medium flex items-center gap-1">Learn more <ChevronRight size={10} /></span>
        </div>
      </div>
    </div>
  )
}
