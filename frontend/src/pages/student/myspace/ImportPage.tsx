/**
 * My Space › Import — the dedicated "upload a file, Uni reads it, complete the
 * gaps" surface (sits between Overview and Profile in the rail).
 *
 * One organized place for the whole flow: upload → review → Uni's grouped
 * follow-up questions → it all lands in your profile. The same flow is also
 * reachable inline in the Uni chat; this is its home.
 */
import { useQueryClient } from '@tanstack/react-query'
import { FileText, ListChecks, Sparkles, Upload } from 'lucide-react'

import MaterialUpload from '../../../components/student/MaterialUpload'
import { PageContainer, PageHeader } from '../../../components/student/density'
import Card from '../../../components/ui/Card'

const STEPS = [
  { icon: Upload, label: 'Upload', sub: 'A resume, transcript, or CV — any format.' },
  { icon: Sparkles, label: 'Uni reads it', sub: 'It extracts your details, grounded in the file.' },
  { icon: FileText, label: 'Review', sub: 'You confirm everything before it is saved.' },
  { icon: ListChecks, label: 'Fill the gaps', sub: 'Uni asks about anything the file left out.' },
]

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
        sub="Upload a resume, transcript, or CV — Uni reads it and fills your profile, then asks about anything it couldn't find. You review everything before it's saved."
      />

      <Card variant="card" pad>
        <div className="grid gap-x-5 gap-y-3 sm:grid-cols-2">
          {STEPS.map((s, i) => (
            <div key={s.label} className="flex items-start gap-2">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-secondary">
                <s.icon size={15} />
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">
                  {i + 1}. {s.label}
                </p>
                <p className="text-xs text-muted-foreground">{s.sub}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 border-t border-border pt-4">
          <MaterialUpload onApplied={refreshProfile} />
        </div>
      </Card>
    </PageContainer>
  )
}
