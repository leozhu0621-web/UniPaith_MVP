// Resources › International (Spec 2026-06-14). A blend: an authored guide to
// studying in the US on a visa, plus a personalized readiness checklist read
// from the student's real profile fields. The readiness panel leads (it's
// actionable); the guide follows as reference.
import ReadinessPanel from './ReadinessPanel'
import GuideSections from './GuideSections'
import { INTL_GUIDE, INTL_GUIDE_DISCLAIMER } from './intlGuide'

export default function ResourcesInternational() {
  return (
    <div className="space-y-5">
      <ReadinessPanel />
      <GuideSections sections={INTL_GUIDE} disclaimer={INTL_GUIDE_DISCLAIMER} />
    </div>
  )
}
