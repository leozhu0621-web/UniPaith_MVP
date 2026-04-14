import { Sparkles, ChevronRight } from 'lucide-react'
import type { Promotion } from '../../../../types'

interface Props {
  promo: Promotion
  onView: () => void
}

export default function PromoCard({ promo, onView }: Props) {
  return (
    <div onClick={onView} className="bg-gradient-to-r from-gold-soft to-white rounded-xl border border-gold/20 hover:shadow-md transition-shadow overflow-hidden cursor-pointer">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Sparkles size={12} className="text-gold" />
        <span className="text-[10px] font-semibold text-gold uppercase tracking-wider">Featured Program</span>
      </div>
      <div className="px-4 pb-4">
        <h3 className="text-sm font-semibold text-student-ink mb-1">{promo.title}</h3>
        {promo.description && <p className="text-xs text-student-text line-clamp-2 mb-2">{promo.description}</p>}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-student-text">{(promo as any).institution_name || ''}</span>
          <span className="text-xs text-gold font-medium flex items-center gap-1">Learn more <ChevronRight size={10} /></span>
        </div>
      </div>
    </div>
  )
}
