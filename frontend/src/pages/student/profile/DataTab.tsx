/**
 * Profile → Data Rights tab (Spec/08 §16, §24; 46 §2/§8).
 * 4 consent levers · portable export (JSON + PDF) · Common App export ·
 * LinkedIn import · access log · danger-zone account deletion.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Download, FileJson, FileText, Link2, Loader2 } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import Input from '../../../components/ui/Input'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import {
  createOnlinePresence,
  exportProfileJson,
  getAccessLog,
  getDataRights,
  getProfile,
  upsertDataRights,
} from '../../../api/students'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import { SectionHeader, Toggle, relativeShort } from './shared'

const LEVERS: { key: string; label: string; help: string }[] = [
  {
    key: 'consent_matching',
    label: 'Matching',
    help: 'Use my profile to power matches and the AI that explains them.',
  },
  {
    key: 'consent_outreach',
    label: 'Outreach',
    help: 'Let institutions I engage with send me messages and campaigns.',
  },
  {
    key: 'consent_research',
    label: 'Analytics',
    help: 'Include my de-identified, aggregated activity in cross-cohort insights.',
  },
  {
    key: 'consent_training',
    label: 'Model training',
    help: 'Include my data in any future UniPaith model-training corpus.',
  },
  {
    key: 'consent_peer_connect',
    label: 'Peer connections',
    help: 'Let other applicants find you by shared programs. Only what you choose to share is visible — never scores or financials.',
  },
]

function buildCommonApp(p: any): { mapped: Record<string, any>; unmapped: string[] } {
  const latestAcademic = (p.academic_records ?? [])[0]
  const mapped: Record<string, any> = {
    'personal.legal_name': [p.first_name, p.last_name].filter(Boolean).join(' ') || null,
    'personal.date_of_birth': p.date_of_birth ?? null,
    'personal.citizenship': p.nationality ?? null,
    'contact.country': p.country_of_residence ?? null,
    'education.current_institution': latestAcademic?.institution_name ?? null,
    'education.gpa': latestAcademic?.gpa ?? null,
    'education.gpa_scale': latestAcademic?.gpa_scale ?? null,
    'testing.scores': (p.test_scores ?? []).map((t: any) => ({ test: t.test_type, score: t.total_score })),
    'activities': (p.activities ?? []).map((a: any) => ({
      type: a.activity_type,
      position: a.title,
      organization: a.organization,
      hours_per_week: a.hours_per_week,
    })),
    'writing.languages': (p.languages ?? []).map((l: any) => ({ language: l.language, proficiency: l.proficiency_level })),
  }
  // Fields we deliberately surface as not-yet-mapped so nothing is silently dropped.
  const unmapped = [
    'personal.ssn',
    'personal.address (street-level)',
    'family.parent_education',
    'courses_and_grades (per-term)',
    'honors',
    'disciplinary_history',
  ]
  return { mapped, unmapped }
}

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function openPrintablePdf(p: any) {
  const esc = (s: any) => String(s ?? '—').replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c] as string))
  const section = (title: string, rows: string) =>
    `<h2 style="font-size:14px;letter-spacing:.04em;text-transform:uppercase;color:#2A6BD4;margin:24px 0 8px">${title}</h2>${rows}`
  const list = (items: string[]) => (items.length ? `<ul style="margin:0;padding-left:18px">${items.map(i => `<li>${i}</li>`).join('')}</ul>` : '<p style="color:#6B6660">—</p>')
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>UniPaith profile</title>
    <style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#2A2724;max-width:720px;margin:40px auto;padding:0 24px;line-height:1.5}
    h1{font-size:28px;margin:0}p{margin:2px 0}</style></head><body>
    <h1>${esc([p.first_name, p.last_name].filter(Boolean).join(' ') || 'Your profile')}</h1>
    <p style="color:#6B6660">${esc(p.country_of_residence)} · ${esc(p.nationality)}</p>
    ${section('Academics', list((p.academic_records ?? []).map((r: any) => `${esc(r.institution_name)} — ${esc(r.degree_type)} ${esc(r.field_of_study)} (GPA ${esc(r.gpa)}/${esc(r.gpa_scale)})`)))}
    ${section('Test scores', list((p.test_scores ?? []).map((t: any) => `${esc(t.test_type)}: ${esc(t.total_score)}`)))}
    ${section('Activities', list((p.activities ?? []).map((a: any) => `${esc(a.title)} — ${esc(a.organization)}`)))}
    ${section('Languages', list((p.languages ?? []).map((l: any) => `${esc(l.language)} (${esc(l.proficiency_level)})`)))}
    ${section('Research', list((p.research_entries ?? []).map((r: any) => esc(r.title))))}
    <p style="margin-top:32px;color:#9A938A;font-size:12px">Generated by UniPaith · ${new Date().toLocaleDateString()}</p>
    </body></html>`
  const w = window.open('', '_blank')
  if (!w) {
    showToast('Allow pop-ups to download the PDF.', 'error')
    return
  }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 300)
}

export default function DataTab() {
  const qc = useQueryClient()
  const { data: dataRights, isLoading } = useQuery({ queryKey: ['data-rights'], queryFn: getDataRights, retry: false })
  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: accessLog } = useQuery({ queryKey: ['access-log'], queryFn: getAccessLog, retry: false })
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [linkedinOpen, setLinkedinOpen] = useState(false)
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [exporting, setExporting] = useState(false)

  const consentMut = useMutation({
    mutationFn: upsertDataRights,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data-rights'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
      qc.invalidateQueries({ queryKey: ['peers-status'] })
      qc.invalidateQueries({ queryKey: ['peers-discover'] })
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })
  const linkedinMut = useMutation({
    mutationFn: () => createOnlinePresence({ platform_type: 'linkedin', url: linkedinUrl, display_name: 'LinkedIn' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      setLinkedinOpen(false)
      setLinkedinUrl('')
      showToast('LinkedIn connected — add your roles under Experience.', 'success')
    },
    onError: () => showToast("Couldn't connect LinkedIn. Check the URL.", 'error'),
  })
  const deleteMut = useMutation({
    mutationFn: () => upsertDataRights({ deletion_requested: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data-rights'] })
      setDeleteOpen(false)
      showToast('Deletion requested. You have 30 days to reverse it.', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  if (isLoading) return <div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>

  // Spec 46 §2 defaults when no consent row exists yet: matching on; the
  // other three opt-in (off). On first change we persist the full set so the
  // stored row matches exactly what's shown.
  const DEFAULTS = {
    consent_matching: true,
    consent_outreach: false,
    consent_research: false,
    consent_training: false,
  }
  const dr: any = dataRights ?? DEFAULTS
  const lastChanged = dataRights?.updated_at ? relativeShort(dataRights.updated_at) : null
  const logEntries: any[] = Array.isArray(accessLog) ? accessLog : []
  const onToggle = (key: string, v: boolean) =>
    consentMut.mutate(dataRights ? { [key]: v } : { ...DEFAULTS, [key]: v })

  const handleJson = async () => {
    try {
      await exportProfileJson()
      showToast('Profile exported', 'success')
    } catch {
      showToast('Export failed. Try again.', 'error')
    }
  }
  const handleCommonApp = () => {
    if (!profile) return
    const payload = buildCommonApp(profile)
    downloadBlob(JSON.stringify(payload, null, 2), 'unipaith-commonapp.json', 'application/json')
    showToast('Common App export downloaded', 'success')
  }
  const handlePdf = async () => {
    setExporting(true)
    try {
      const p = profile ?? (await getProfile())
      openPrintablePdf(p)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="space-y-10">
      {/* Consent levers */}
      <section>
        <SectionHeader title="Consent" description="Independent controls over how your data is used." />
        <Card pad={false} className="divide-y divide-border">
          {LEVERS.map(lever => (
            <div key={lever.key} className="flex items-start justify-between gap-4 p-4">
              <div className="min-w-0">
                <label htmlFor={lever.key} className="font-semibold text-foreground">{lever.label}</label>
                <p className="text-sm text-muted-foreground">{lever.help}</p>
                {/* Spec 46 §8 — objecting to AI processing has a clear consequence. */}
                {lever.key === 'consent_matching' && !dr.consent_matching && (
                  <p className="text-xs text-warning mt-1.5">
                    With matching off, no AI runs on your data — no personalized matches, no “why”
                    explanations, and no Discovery chat. You can still browse anonymously.
                  </p>
                )}
                {lastChanged && <p className="text-xs text-muted-foreground mt-1">Last changed {lastChanged}</p>}
              </div>
              <Toggle
                id={lever.key}
                checked={Boolean(dr[lever.key])}
                disabled={consentMut.isPending}
                onChange={v => onToggle(lever.key, v)}
              />
            </div>
          ))}
        </Card>
        {/* Spec 46 §2 — every consent change is logged. */}
        <p className="text-xs text-muted-foreground mt-2">
          Every change is recorded in your <span className="font-medium text-foreground">access log</span> below.
        </p>
      </section>

      {/* Portable export */}
      <section>
        <SectionHeader title="Export your data" description="Take your work anywhere — your record is yours." />
        <div className="grid sm:grid-cols-2 gap-3">
          <Card pad={false} className="p-5 flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2"><FileJson size={16} className="text-secondary" /><p className="font-semibold text-foreground">Full data (JSON)</p></div>
              <p className="text-sm text-muted-foreground mt-1">Every signal in a structured, portable file.</p>
            </div>
            <Button size="sm" variant="tertiary" onClick={handleJson}><Download size={14} /> JSON</Button>
          </Card>
          <Card pad={false} className="p-5 flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2"><FileText size={16} className="text-secondary" /><p className="font-semibold text-foreground">Human-readable (PDF)</p></div>
              <p className="text-sm text-muted-foreground mt-1">A printable summary of your profile.</p>
            </div>
            <Button size="sm" variant="tertiary" onClick={handlePdf} disabled={exporting}>
              {exporting ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />} PDF
            </Button>
          </Card>
          <Card pad={false} className="p-5 flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2"><FileJson size={16} className="text-secondary" /><p className="font-semibold text-foreground">Common App format</p></div>
              <p className="text-sm text-muted-foreground mt-1">Map your record onto Common App fields. Unmapped fields are listed so nothing is dropped.</p>
            </div>
            <Button size="sm" variant="tertiary" onClick={handleCommonApp}><Download size={14} /> Export</Button>
          </Card>
          <Card pad={false} className="p-5 flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2"><Link2 size={16} className="text-secondary" /><p className="font-semibold text-foreground">Import from LinkedIn</p></div>
              <p className="text-sm text-muted-foreground mt-1">One-way: connect your LinkedIn so you can fill work and education faster.</p>
            </div>
            <Button size="sm" variant="tertiary" onClick={() => setLinkedinOpen(true)}>Connect</Button>
          </Card>
        </div>
      </section>

      {/* Access log */}
      <section>
        <SectionHeader title="Access log" description="Who and what touched your data, and when." />
        {logEntries.length === 0 ? (
          <Card pad={false} className="p-5"><p className="text-sm text-muted-foreground">No access recorded yet. Activity on your data — by you, the institutions you apply to, and AI — will appear here.</p></Card>
        ) : (
          <Card pad={false} className="p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground bg-muted">
                  <th className="px-4 py-2.5 font-semibold">When</th>
                  <th className="px-4 py-2.5 font-semibold">Who</th>
                  <th className="px-4 py-2.5 font-semibold">Action</th>
                  <th className="px-4 py-2.5 font-semibold">Fields</th>
                </tr>
              </thead>
              <tbody>
                {logEntries.slice(0, 25).map((e, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="px-4 py-2.5 text-muted-foreground whitespace-nowrap">{relativeShort(e.timestamp) ?? formatDate(e.timestamp)}</td>
                    <td className="px-4 py-2.5 text-foreground">{e.actor}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{e.action}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{e.fields}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      {/* Danger zone */}
      <section>
        <SectionHeader title="Danger zone" />
        <Card pad={false} className="p-5 border-error/40">
          {dr.deletion_requested ? (
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-semibold text-foreground">Deletion requested</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Your account is scheduled for deletion. You can reverse this within the 30-day grace period.
                </p>
              </div>
              <Button size="sm" variant="tertiary" onClick={() => deleteMut.mutate()} loading={deleteMut.isPending}>Keep my account</Button>
            </div>
          ) : (
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-semibold text-foreground">Delete account</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Permanently remove your account and all profile data after a 30-day grace period.
                </p>
              </div>
              <Button size="sm" variant="destructive" onClick={() => setDeleteOpen(true)}>Delete account</Button>
            </div>
          )}
        </Card>
      </section>

      {/* Delete confirm */}
      <Modal isOpen={deleteOpen} onClose={() => setDeleteOpen(false)} title="Delete account">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-error shrink-0 mt-0.5" />
            <p className="text-sm text-foreground">
              Are you sure? Your account and all profile data will be permanently deleted after a 30-day grace period.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={() => deleteMut.mutate()} loading={deleteMut.isPending}>Delete account</Button>
          </div>
        </div>
      </Modal>

      {/* LinkedIn connect */}
      <Modal isOpen={linkedinOpen} onClose={() => setLinkedinOpen(false)} title="Connect LinkedIn">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Paste your public LinkedIn URL. We'll save it to your profile so you can mirror your roles and education
            under Experience. Import is one-way — UniPaith never posts to LinkedIn.
          </p>
          <Input label="LinkedIn URL" placeholder="https://www.linkedin.com/in/you" value={linkedinUrl} onChange={e => setLinkedinUrl(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setLinkedinOpen(false)}>Cancel</Button>
            <Button onClick={() => linkedinMut.mutate()} loading={linkedinMut.isPending} disabled={!linkedinUrl.trim()}>Connect</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
