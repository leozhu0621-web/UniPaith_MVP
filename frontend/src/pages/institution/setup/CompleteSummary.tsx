import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Circle } from 'lucide-react'
import type { Institution, InstitutionSetupState } from '../../../types'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'

function Row({ done, label, hint }: { done: boolean; label: string; hint: string }) {
  return (
    <li className="flex items-center gap-3 py-2">
      {done ? (
        <CheckCircle2 size={18} className="shrink-0 text-success" />
      ) : (
        <Circle size={18} className="shrink-0 text-muted-foreground" />
      )}
      <span className="text-sm font-medium text-foreground">{label}</span>
      <span className="ml-auto text-xs text-muted-foreground">{hint}</span>
    </li>
  )
}

// Spec 30 §6 — once complete, /i/setup is a read-only summary with edit links
// (not forced).
export default function CompleteSummary({
  institution,
  setupState,
}: {
  institution: Institution | null
  setupState: InstitutionSetupState
}) {
  const navigate = useNavigate()
  const sc = setupState.steps_complete
  const published = setupState.published_program_count

  return (
    <Card pad={false} className="p-6 sm:p-8">
      <div className="text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-success-soft text-success">
          <CheckCircle2 size={26} />
        </span>
        <h2 className="mt-3 text-xl font-semibold text-foreground">
          {institution?.name ? `${institution.name} is set up` : 'Your institution is set up'}
        </h2>
      </div>

      <ul className="mx-auto mt-6 max-w-md divide-y divide-border">
        <Row done={sc.profile} label="Profile" hint={sc.profile ? 'Published' : 'Incomplete'} />
        <Row
          done={sc.program}
          label="First program"
          hint={published > 0 ? `${published} published` : sc.program ? 'Draft' : 'None yet'}
        />
        <Row done={sc.data} label="Data" hint={setupState.skipped.data && published >= 0 ? 'Optional' : sc.data ? 'Uploaded' : 'Optional'} />
        <Row done={sc.team} label="Team" hint={sc.team ? 'Invited' : 'Optional'} />
      </ul>

      <div className="mt-7 flex flex-wrap items-center justify-center gap-2">
        <Button variant="secondary" onClick={() => navigate('/i/dashboard')}>
          Go to dashboard
        </Button>
        <Button variant="tertiary" onClick={() => navigate('/i/settings')}>
          Edit profile in Settings
        </Button>
        <Button variant="tertiary" onClick={() => navigate('/i/programs')}>
          Manage programs
        </Button>
      </div>
    </Card>
  )
}
