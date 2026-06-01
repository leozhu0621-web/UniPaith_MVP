import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, FileText, Users, Info } from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import { createCampaign, updateCampaign, draftCampaignCopy } from '../../../api/institutions'
import type {
  Campaign,
  CampaignChannel,
  CampaignDestinationType,
  CommunicationTemplate,
  Program,
  Segment,
  UploadedList,
} from '../../../types'
import { showToast } from '../../../stores/toast-store'
import {
  CHANNEL_OPTIONS,
  CTA_OPTIONS,
  DESTINATION_OPTIONS,
  OBJECTIVE_OPTIONS,
  PERSONALIZATION_TOKENS,
} from './constants'

interface Props {
  isOpen: boolean
  onClose: () => void
  editTarget: Campaign | null
  programs: Program[]
  segments: Segment[]
  uploadedLists: UploadedList[]
  templates: CommunicationTemplate[]
  onSaved: () => void
}

interface FormState {
  name: string
  objective: string
  channels: CampaignChannel[]
  associate_program_ids: string[]
  destination_type: string
  destination_url: string
  cta_type: string
  audience_segment_ids: string[]
  audience_uploaded_list_ids: string[]
  subject: string
  body: string
  scheduled_at: string
}

const EMPTY: FormState = {
  name: '',
  objective: 'general',
  channels: ['internal_messaging'],
  associate_program_ids: [],
  destination_type: 'institution_page',
  destination_url: '',
  cta_type: 'learn_more',
  audience_segment_ids: [],
  audience_uploaded_list_ids: [],
  subject: '',
  body: '',
  scheduled_at: '',
}

function ChipMultiSelect({
  options,
  selected,
  onToggle,
  empty,
}: {
  options: { value: string; label: string }[]
  selected: string[]
  onToggle: (v: string) => void
  empty: string
}) {
  if (options.length === 0) return <p className="text-xs text-muted-foreground">{empty}</p>
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = selected.includes(o.value)
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onToggle(o.value)}
            aria-pressed={on}
            className={clsx(
              'px-3 py-1.5 rounded-full text-[13px] border transition-colors',
              on
                ? 'bg-secondary text-secondary-foreground border-transparent'
                : 'bg-card text-foreground border-border hover:bg-muted',
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-[13px] font-semibold text-foreground">{label}</label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

export default function CampaignEditorModal({
  isOpen,
  onClose,
  editTarget,
  programs,
  segments,
  uploadedLists,
  templates,
  onSaved,
}: Props) {
  const [form, setForm] = useState<FormState>(EMPTY)
  const [altSubjects, setAltSubjects] = useState<string[]>([])
  const set = <K extends keyof FormState>(k: K, v: FormState[K]) => setForm((f) => ({ ...f, [k]: v }))
  const toggleIn = (k: 'associate_program_ids' | 'audience_segment_ids' | 'audience_uploaded_list_ids' | 'channels', v: string) =>
    setForm((f) => {
      const arr = f[k] as string[]
      return { ...f, [k]: arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v] }
    })

  useEffect(() => {
    if (!isOpen) return
    setAltSubjects([])
    if (editTarget) {
      setForm({
        name: editTarget.name,
        objective: editTarget.objective ?? 'general',
        channels: editTarget.channels?.length ? editTarget.channels : ['internal_messaging'],
        associate_program_ids: editTarget.associate_program_ids ?? [],
        destination_type: editTarget.destination_type ?? 'institution_page',
        destination_url: editTarget.destination_url ?? '',
        cta_type: editTarget.cta_type ?? 'learn_more',
        audience_segment_ids: editTarget.audience?.segment_ids ?? [],
        audience_uploaded_list_ids: editTarget.audience?.uploaded_list_ids ?? [],
        subject: editTarget.subject ?? '',
        body: editTarget.body ?? '',
        scheduled_at: editTarget.scheduled_at ? editTarget.scheduled_at.slice(0, 16) : '',
      })
    } else {
      setForm(EMPTY)
    }
  }, [isOpen, editTarget])

  const wantsExternal = form.channels.includes('external_email')

  const draftMut = useMutation({
    mutationFn: () =>
      draftCampaignCopy({
        objective: form.objective,
        cta_type: form.cta_type,
        audience_segment_ids: form.audience_segment_ids,
      }),
    onSuccess: (d) => {
      setForm((f) => ({ ...f, subject: d.subject, body: d.body }))
      setAltSubjects(d.alternate_subjects || [])
      showToast(d.source === 'llm' ? 'Drafted with AI' : 'Draft ready', 'success')
    },
    onError: () => showToast('Could not draft copy', 'error'),
  })

  const saveMut = useMutation({
    mutationFn: () => {
      const payload = {
        name: form.name.trim(),
        objective: form.objective as any,
        channels: form.channels,
        associate_program_ids: form.associate_program_ids,
        destination_type: form.destination_type as CampaignDestinationType,
        destination_url: form.destination_url || null,
        cta_type: form.cta_type as any,
        audience_segment_ids: form.audience_segment_ids,
        audience_uploaded_list_ids: form.audience_uploaded_list_ids,
        subject: form.subject || null,
        body: form.body || null,
        scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
      }
      return editTarget ? updateCampaign(editTarget.id, payload) : createCampaign(payload)
    },
    onSuccess: () => {
      showToast(editTarget ? 'Campaign updated' : 'Campaign created', 'success')
      onSaved()
      onClose()
    },
    onError: () => showToast('Could not save campaign', 'error'),
  })

  const applyTemplate = (id: string) => {
    const t = templates.find((x) => x.id === id)
    if (!t) return
    setForm((f) => ({ ...f, subject: t.subject || f.subject, body: t.body || f.body }))
    showToast(`Started from “${t.name}”`, 'success')
  }

  const handleSave = () => {
    if (!form.name.trim()) return showToast('Name is required', 'warning')
    if (form.channels.length === 0) return showToast('Select at least one channel', 'warning')
    saveMut.mutate()
  }

  const programOpts = useMemo(
    () => programs.map((p) => ({ value: p.id, label: p.program_name })),
    [programs],
  )
  const segmentOpts = useMemo(
    () => segments.map((s) => ({ value: s.id, label: s.segment_name })),
    [segments],
  )
  const listOpts = useMemo(
    () => uploadedLists.map((l) => ({ value: l.id, label: `${l.name} · ${l.contact_count}` })),
    [uploadedLists],
  )
  const templateOpts = [
    { value: '', label: 'Start from template…' },
    ...templates.map((t) => ({ value: t.id, label: t.name })),
  ]

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editTarget ? 'Edit campaign' : 'New campaign'}
      size="lg"
    >
      <div className="space-y-5 max-h-[70vh] overflow-y-auto pr-1">
        <Field label="Campaign name">
          <Input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Fall open house outreach" />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Objective">
            <Select options={OBJECTIVE_OPTIONS} value={form.objective} onChange={(e) => set('objective', e.target.value)} />
          </Field>
          <Field label="Call to action">
            <Select options={CTA_OPTIONS} value={form.cta_type} onChange={(e) => set('cta_type', e.target.value)} />
          </Field>
        </div>

        <Field label="Channels" hint={CHANNEL_OPTIONS.find((c) => form.channels.includes(c.value))?.hint}>
          <div className="flex flex-wrap gap-2">
            {CHANNEL_OPTIONS.map((c) => {
              const on = form.channels.includes(c.value)
              return (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => toggleIn('channels', c.value)}
                  aria-pressed={on}
                  className={clsx(
                    'px-3 py-1.5 rounded-full text-[13px] border transition-colors',
                    on ? 'bg-secondary text-secondary-foreground border-transparent' : 'bg-card text-foreground border-border hover:bg-muted',
                  )}
                >
                  {c.label}
                </button>
              )
            })}
          </div>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Destination">
            <Select options={DESTINATION_OPTIONS} value={form.destination_type} onChange={(e) => set('destination_type', e.target.value)} />
          </Field>
          {form.destination_type === 'external_url' && (
            <Field label="Destination URL">
              <Input value={form.destination_url} onChange={(e) => set('destination_url', e.target.value)} placeholder="https://…" />
            </Field>
          )}
        </div>

        <Field label="Associated programs" hint="Optional — ties metrics and the program link to specific programs.">
          <ChipMultiSelect
            options={programOpts}
            selected={form.associate_program_ids}
            onToggle={(v) => toggleIn('associate_program_ids', v)}
            empty="No programs yet."
          />
        </Field>

        <div className="rounded-lg border border-border bg-muted/40 p-3 space-y-3">
          <div className="flex items-center gap-2 text-[13px] font-semibold text-foreground">
            <Users size={15} className="text-accent" /> Audience
          </div>
          <Field label="Segments">
            <ChipMultiSelect
              options={segmentOpts}
              selected={form.audience_segment_ids}
              onToggle={(v) => toggleIn('audience_segment_ids', v)}
              empty="No saved segments. Build one in Communications → Segments."
            />
          </Field>
          <Field label="Uploaded lists" hint="External email only. Deduped by email against platform users; suppression honored.">
            <ChipMultiSelect
              options={listOpts}
              selected={form.audience_uploaded_list_ids}
              onToggle={(v) => toggleIn('audience_uploaded_list_ids', v)}
              empty="No uploaded lists. Add one from “Manage audience”."
            />
          </Field>
          {form.audience_segment_ids.length === 0 && form.audience_uploaded_list_ids.length === 0 && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Info size={12} /> With no audience selected, the campaign targets applicants of the associated programs.
            </p>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[13px] font-semibold text-foreground">Message</span>
          <div className="flex items-center gap-2">
            {templates.length > 0 && (
              <select
                className="h-8 rounded-lg border border-border bg-card text-[13px] px-2 text-foreground"
                value=""
                onChange={(e) => e.target.value && applyTemplate(e.target.value)}
                aria-label="Start from template"
              >
                {templateOpts.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )}
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => draftMut.mutate()}
              loading={draftMut.isPending}
              className="gap-1"
            >
              <Sparkles size={14} /> Draft with AI
            </Button>
          </div>
        </div>

        {wantsExternal && (
          <Field label="Subject">
            <Input value={form.subject} onChange={(e) => set('subject', e.target.value)} placeholder="A subject worth opening" />
          </Field>
        )}
        {altSubjects.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground">Alternates:</span>
            {altSubjects.map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => set('subject', s)}
                className="text-xs px-2 py-1 rounded-md border border-border text-accent hover:bg-muted"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <Field label="Body">
          <Textarea value={form.body} onChange={(e) => set('body', e.target.value)} rows={6} placeholder="Write your outreach message…" />
        </Field>
        <div className="rounded-md bg-muted/60 px-3 py-2 flex items-start gap-2">
          <FileText size={13} className="text-muted-foreground mt-0.5" />
          <p className="text-xs text-muted-foreground">
            Personalization: {PERSONALIZATION_TOKENS.join(', ')} are substituted at send time. An
            unsubscribe link is appended to every email automatically.
          </p>
        </div>

        <Field label="Schedule send" hint="Optional. Leave empty to send manually.">
          <Input type="datetime-local" value={form.scheduled_at} onChange={(e) => set('scheduled_at', e.target.value)} />
        </Field>
      </div>

      <div className="flex justify-end gap-2 pt-4 mt-2 border-t border-border">
        <Button variant="tertiary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="secondary" onClick={handleSave} loading={saveMut.isPending}>
          {editTarget ? 'Save changes' : 'Create campaign'}
        </Button>
      </div>
    </Modal>
  )
}
