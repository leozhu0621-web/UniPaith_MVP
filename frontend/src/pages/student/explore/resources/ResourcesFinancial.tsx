// Resources › Financial (Spec 2026-06-14). An authored "how aid works" guide
// (general, not personalized) paired with a CTA to the student's REAL per-program
// cost comparison — that surface holds the actual numbers; this explains them.
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Calculator } from 'lucide-react'
import GuideSections from './GuideSections'
import { AID_GUIDE, AID_GUIDE_DISCLAIMER } from './aidGuide'

export default function ResourcesFinancial() {
  const navigate = useNavigate()
  return (
    <div>
      <GuideSections sections={AID_GUIDE} disclaimer={AID_GUIDE_DISCLAIMER} />

      {/* Hand-off to the real, personalized cost comparison. */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-5">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-sm font-bold text-foreground">
            <Calculator size={15} className="text-secondary" aria-hidden /> Compare your real costs
          </p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            See net price, tuition, and affordability across the programs you’ve saved and applied to.
          </p>
        </div>
        <button
          onClick={() => navigate('/s/applications?tab=costs')}
          className="ui-btn inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-secondary px-3 py-2 text-sm font-medium text-secondary-foreground"
        >
          Costs & aid <ArrowRight size={14} />
        </button>
      </div>
    </div>
  )
}
