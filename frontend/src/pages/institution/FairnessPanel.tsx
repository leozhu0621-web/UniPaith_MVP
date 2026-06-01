import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { getFairness, overrideFairnessHalt, type ProgramFairnessStatus } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { showToast } from '../../stores/toast-store'

const ATTR_LABEL: Record<string, string> = {
  gender_identity: 'Gender',
  nationality: 'Nationality',
  first_generation_status: 'First-generation',
}

/**
 * Dashboard fairness panel (G-I5 / Spec 43 §6). Surfaces programs whose
 * matching was auto-halted for disparate impact, plus any program with a
 * breached-but-not-yet-halted signal (approaching threshold). Halted programs
 * get a human override workflow (audit-logged server-side). Renders nothing
 * when everything is within threshold, so it reads as an alert.
 */
export default function FairnessPanel() {
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: ['fairness'], queryFn: getFairness, retry: false })
  const [reasons, setReasons] = useState<Record<string, string>>({})

  const overrideMut = useMutation({
    mutationFn: ({ programId, reason }: { programId: string; reason: string }) =>
      overrideFairnessHalt(programId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fairness'] })
      showToast('Matching halt cleared', 'success')
    },
    onError: () => showToast('Could not clear the halt', 'error'),
  })

  if (!data) return null
  const halted = data.filter(p => p.matching_halted)
  const approaching = data.filter(
    p => !p.matching_halted && p.signals.some(s => s.breached),
  )
  if (halted.length === 0 && approaching.length === 0) return null

  const worstDelta = (p: ProgramFairnessStatus) =>
    Math.max(0, ...p.signals.map(s => s.disparate_impact_delta ?? 0))

  return (
    <Card className="p-4 border-l-4 border-l-error">
      <div className="flex items-center gap-2 mb-3">
        <ShieldAlert size={16} className="text-error" />
        <h3 className="text-sm font-semibold text-charcoal">Fairness &amp; bias</h3>
        <span className="text-xs text-slate">Disparate-impact monitoring (4/5ths rule)</span>
      </div>

      {halted.map(p => (
        <div key={p.program_id} className="mb-3 rounded-md border border-error/30 bg-error-soft/40 p-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-error">
                Matching halted · {p.program_name}
              </p>
              <p className="text-xs text-slate mt-0.5">
                Disparate impact breached threshold for 2 consecutive weeks. New applicants
                are not being scored for this program until you review and override.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {p.signals.filter(s => s.breached).slice(0, 4).map((s, i) => (
                  <span key={i} className="text-[10px] rounded-sm bg-white border border-error/30 px-1.5 py-0.5 text-error">
                    {ATTR_LABEL[s.protected_attribute] ?? s.protected_attribute}: Δ{((s.disparate_impact_delta ?? 0) * 100).toFixed(0)}%
                    {s.disadvantaged_group ? ` (${s.disadvantaged_group})` : ''}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-2.5 flex items-center gap-2">
            <input
              value={reasons[p.program_id] ?? ''}
              onChange={e => setReasons(r => ({ ...r, [p.program_id]: e.target.value }))}
              placeholder="Reason for overriding the halt (audit-logged)"
              className="flex-1 text-xs border border-stone rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-cobalt/40"
            />
            <Button
              size="sm"
              variant="secondary"
              loading={overrideMut.isPending}
              disabled={(reasons[p.program_id] ?? '').trim().length < 3}
              onClick={() => overrideMut.mutate({ programId: p.program_id, reason: reasons[p.program_id] })}
            >
              Override halt
            </Button>
          </div>
        </div>
      ))}

      {approaching.map(p => (
        <div key={p.program_id} className="mb-2 flex items-center gap-2 rounded-md border border-warning/30 bg-warning-soft/40 px-3 py-2">
          <ShieldCheck size={14} className="text-warning flex-shrink-0" />
          <p className="text-xs text-charcoal flex-1">
            <span className="font-semibold">{p.program_name}</span> · a protected group is
            approaching the disparate-impact threshold (Δ{(worstDelta(p) * 100).toFixed(0)}%). One more
            breached week halts matching.
          </p>
        </div>
      ))}
    </Card>
  )
}
