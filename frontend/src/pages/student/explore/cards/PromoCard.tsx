import { Link } from 'react-router-dom'
import { Sparkles, ChevronRight } from 'lucide-react'
import type { Promotion } from '../../../../types'
import { cardLinkClick, CARD_LINK_OVERLAY } from '../shared/cardLink'

interface Props {
  promo: Promotion
  onView: () => void
}

// Featured/promoted program — gold is the earned "featured" punctuation (eyebrow
// + left accent), but no gradient fill (brand: gold is punctuation, not fill).
//
// Ship D §4 — the card is a real link (stretched title link over the card):
// keyboard focus, Enter, and cmd/ctrl-click open-in-new-tab all work. Plain
// clicks still route through onView so the promotion click is recorded.
export default function PromoCard({ promo, onView }: Props) {
  const to = promo.program_id ? `/s/programs/${promo.program_id}` : null
  const external = !to && promo.target_url ? promo.target_url : null

  const title = to ? (
    <Link to={to} onClick={cardLinkClick(onView)} className={CARD_LINK_OVERLAY}>
      {promo.title}
    </Link>
  ) : external ? (
    <a
      href={external}
      target="_blank"
      rel="noopener noreferrer"
      onClick={cardLinkClick(onView)}
      className={CARD_LINK_OVERLAY}
    >
      {promo.title}
    </a>
  ) : (
    promo.title
  )
  const linked = to !== null || external !== null

  return (
    <div
      onClick={linked ? undefined : onView}
      className={`relative bg-card rounded-lg border border-border border-l-2 border-l-secondary hover-lift hover:elev-raised overflow-hidden ${linked ? '' : 'cursor-pointer'}`}
    >
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Sparkles size={12} className="text-secondary" />
        <span className="text-[10px] font-semibold text-secondary uppercase tracking-wider">Featured program</span>
      </div>
      <div className="px-4 pb-4">
        <h3 className="text-sm font-semibold text-foreground mb-1 break-words">{title}</h3>
        {promo.description && <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{promo.description}</p>}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">{(promo as { institution_name?: string }).institution_name || ''}</span>
          <span className="text-xs text-secondary font-medium flex items-center gap-1">Learn more <ChevronRight size={10} /></span>
        </div>
      </div>
    </div>
  )
}
