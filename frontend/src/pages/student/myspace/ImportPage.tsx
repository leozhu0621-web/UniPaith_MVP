/**
 * My Space › Import — the dedicated "upload a file, Uni reads it, complete the
 * gaps" surface (sits between Overview and Profile in the rail).
 *
 * One organized place for the whole flow: upload → review → Uni's grouped
 * follow-up questions → it all lands in your profile. The same flow is also
 * reachable inline in the Uni chat; this is its home.
 */
import { useQueryClient } from '@tanstack/react-query'

import MaterialUpload from '../../../components/student/MaterialUpload'
import { PageContainer, PageHeader } from '../../../components/student/density'
import Card from '../../../components/ui/Card'

export default function ImportPage() {
  const qc = useQueryClient()

  const refreshProfile = () => {
    // Everything an import can touch — so the Profile reflects it immediately.
    for (const key of [
      ['student', 'profile'],
      ['goals'],
      ['needs'],
      ['identity'],
      ['academics'],
      ['activities'],
      ['work-experiences'],
      ['test-scores'],
      ['languages'],
      ['online-presence'],
      ['discovery', 'completion'],
    ]) {
      qc.invalidateQueries({ queryKey: key })
    }
  }

  return (
    // Focused upload wizard — width-constrained (CLAUDE.md: focused forms/wizards
    // stay narrow, not full-bleed) and wrapped in PageContainer for the standard
    // gutters + page-entrance motion every My Space room uses.
    <PageContainer className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="My Space"
        title="Import"
      />

      <Card variant="card" pad>
        <MaterialUpload onApplied={refreshProfile} />
      </Card>
    </PageContainer>
  )
}
