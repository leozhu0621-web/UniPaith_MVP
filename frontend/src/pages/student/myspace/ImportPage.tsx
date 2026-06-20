import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, FileText, Link2 } from 'lucide-react'

import { getCompleteness, getMatchReady, listClarifications, resolveClarification } from '../../../api/intake'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import FileDropzone from '../profile/FileDropzone'
import usePageTitle from '../../../hooks/usePageTitle'
import { showToast } from '../../../stores/toast-store'

function pct(value?: number | null) {
  return Math.max(0, Math.min(100, Math.round(value ?? 0)))
}

export default function ImportPage() {
  usePageTitle('My Space · Import')
  const queryClient = useQueryClient()
  const completeness = useQuery({ queryKey: ['intake-completeness'], queryFn: getCompleteness })
  const matchReady = useQuery({ queryKey: ['intake-match-ready'], queryFn: getMatchReady })
  const clarifications = useQuery({ queryKey: ['intake-clarifications'], queryFn: listClarifications })

  const confirm = useMutation({
    mutationFn: (id: string) => resolveClarification(id, 'confirm'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intake-clarifications'] })
      queryClient.invalidateQueries({ queryKey: ['intake-completeness'] })
      queryClient.invalidateQueries({ queryKey: ['intake-match-ready'] })
      showToast('Signal confirmed', 'success')
    },
    onError: () => showToast("We couldn't confirm that signal. Try again.", 'error'),
  })

  const completion = pct(completeness.data?.overall_profile_completeness_pct)
  const missing = matchReady.data?.missing ?? []
  const clarificationList = clarifications.data?.clarifications ?? []
  const loading = completeness.isLoading || matchReady.isLoading

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="up-eyebrow">My Space · Import</p>
          <h1 className="text-h1 text-foreground">Bring your materials in</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Upload transcripts, resumes, writing samples, and aid documents. Uni extracts signals, shows confidence,
            and asks you to confirm anything uncertain before it affects matching or applications.
          </p>
        </div>
        <Badge variant={matchReady.data?.match_ready ? 'success' : 'info'}>
          {matchReady.data?.match_ready ? 'Match-ready' : `${completion}% profile coverage`}
        </Badge>
      </header>

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <Card className="p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-h3 text-foreground">Readiness from real evidence</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Coverage uses the Prompt Library and adaptive intake gates, not a decorative checklist.
                </p>
              </div>
              <span className="text-2xl font-semibold tabular-nums text-foreground">{completion}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-pill bg-muted" aria-label={`Profile coverage ${completion}%`}>
              <div className="h-full rounded-pill bg-secondary transition-all" style={{ width: `${completion}%` }} />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <SignalTile label="Present signals" value={completeness.data?.present_signals ?? 0} />
              <SignalTile label="Total tracked" value={completeness.data?.total_signals ?? 0} />
              <SignalTile label="Missing for match" value={missing.length} tone={missing.length ? 'warning' : 'success'} />
            </div>
            {missing.length > 0 && (
              <div className="mt-5">
                <h3 className="mb-2 text-sm font-semibold text-foreground">Highest-impact gaps</h3>
                <div className="space-y-2">
                  {missing.slice(0, 5).map(item => (
                    <div key={`${item.kind}-${item.signal_name}`} className="rounded-md border border-border bg-background px-3 py-2">
                      <p className="text-sm font-medium text-foreground">{item.label}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{item.detail || item.category}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="text-h3 text-foreground">Confirm uncertain signals</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Low-confidence extraction never silently becomes truth. Confirm what is correct, then fill the rest.
            </p>
            <div className="mt-4 space-y-3">
              {clarificationList.length === 0 ? (
                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-foreground">
                    <CheckCircle2 size={16} className="text-success" /> No confirmations waiting
                  </div>
                  <p className="text-sm text-muted-foreground">New clarification tasks will appear here after uploads or chat turns.</p>
                </div>
              ) : (
                clarificationList.slice(0, 4).map(item => (
                  <div key={item.id} className="rounded-lg border border-border bg-background p-4">
                    <div className="mb-2 flex items-start gap-2">
                      <AlertCircle size={16} className="mt-0.5 shrink-0 text-warning" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-foreground">{item.label}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{item.question}</p>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Confidence {Math.round((item.confidence ?? 0) * 100)}%
                        </p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => confirm.mutate(item.id)}
                      loading={confirm.isPending && confirm.variables === item.id}
                    >
                      Confirm
                    </Button>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <UploadCard title="Academic record" description="Transcripts, grade reports, test score PDFs." type="transcript" />
        <UploadCard title="Experience evidence" description="Resume, portfolio, activities, research records." type="resume" />
        <UploadCard title="Application material" description="Essay drafts, writing samples, offer letters, aid docs." type="application_material" />
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2">
        <Card className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <Link2 size={17} className="text-secondary" />
            <h2 className="text-h3 text-foreground">Connect an external source</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            The intake engine supports links, forms, documents, chat, institution-provided facts, and system-derived signals.
            Link ingestion is kept behind the same confirmation loop.
          </p>
          <Button className="mt-4" variant="tertiary" size="sm" disabled>
            External link import coming next
          </Button>
        </Card>
        <Card className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <FileText size={17} className="text-secondary" />
            <h2 className="text-h3 text-foreground">What happens after upload</h2>
          </div>
          <ol className="space-y-2 text-sm text-muted-foreground">
            <li>1. Raw material is stored as evidence.</li>
            <li>2. Signals are normalized with source and confidence.</li>
            <li>3. Low-confidence fields become confirmation tasks.</li>
            <li>4. Match and application readiness update only after validation.</li>
          </ol>
        </Card>
      </section>
    </main>
  )
}

function SignalTile({ label, value, tone = 'default' }: { label: string; value: number; tone?: 'default' | 'success' | 'warning' }) {
  return (
    <div className={`rounded-lg border px-3 py-2 ${tone === 'warning' ? 'border-warning/40 bg-warning-soft/40' : tone === 'success' ? 'border-success/30 bg-success-soft/40' : 'border-border bg-background'}`}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-foreground">{value}</p>
    </div>
  )
}

function UploadCard({ title, description, type }: { title: string; description: string; type: string }) {
  return (
    <Card className="p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
      <FileDropzone documentType={type} label={title} />
    </Card>
  )
}
