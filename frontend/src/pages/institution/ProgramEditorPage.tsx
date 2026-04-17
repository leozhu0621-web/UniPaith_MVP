import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Save, Send } from 'lucide-react'
import { getInstitutionProgram, createProgram, updateProgram, publishProgram } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import { showToast } from '../../stores/toast-store'

const DEGREE_OPTIONS = [
  { value: 'bachelors', label: "Bachelor's" },
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'Ph.D.' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'diploma', label: 'Diploma' },
]

const DELIVERY_FORMAT_OPTIONS = [
  { value: '', label: 'Not specified' },
  { value: 'in_person', label: 'In Person' },
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
]

const CAMPUS_SETTING_OPTIONS = [
  { value: '', label: 'Not specified' },
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
]

const schema = z.object({
  program_name: z.string().min(1, 'Required'),
  degree_type: z.string().min(1, 'Required'),
  department: z.string().optional(),
  duration_months: z.coerce.number().optional(),
  tuition: z.coerce.number().optional(),
  acceptance_rate: z.coerce.number().min(0).max(1).optional(),
  delivery_format: z.string().optional(),
  campus_setting: z.string().optional(),
  application_deadline: z.string().optional(),
  program_start_date: z.string().optional(),
  description_text: z.string().optional(),
  who_its_for: z.string().optional(),
  tracks_concentrations: z.array(z.object({ value: z.string() })).optional(),
  tracks_note: z.string().optional(),
  highlights: z.array(z.object({ value: z.string() })).optional(),
  media_urls: z.array(z.object({ value: z.string() })).optional(),
  requirements: z.array(z.object({ key: z.string(), value: z.string() })).optional(),
  faculty_contacts: z.array(z.object({ name: z.string(), email: z.string().optional(), role: z.string().optional() })).optional(),
})
type FormData = z.infer<typeof schema>

// JSONB fields too varied/nested for per-key widgets — edited as JSON text.
type JsonFieldKey = 'application_requirements' | 'intake_rounds' | 'cost_data' | 'outcomes_data'
const JSON_FIELDS: { key: JsonFieldKey; label: string; placeholder: string; hint: string }[] = [
  {
    key: 'application_requirements',
    label: 'Application Requirements',
    placeholder: '[\n  {"label": "Common Application", "required": true},\n  {"label": "Essay", "required": true}\n]',
    hint: 'JSON array of {label, required, note?}. Surfaces on the student Requirements tab as the Application Checklist.',
  },
  {
    key: 'intake_rounds',
    label: 'Intake Rounds',
    placeholder: '{\n  "fall_2026": {"early_decision_1": {"deadline": "2025-11-01"}, "regular_decision": {"deadline": "2026-01-05"}},\n  "source": "Office of Admissions"\n}',
    hint: 'JSON dict. Shape matches the admissions calendar (e.g., fall_YYYY with early/regular rounds).',
  },
  {
    key: 'cost_data',
    label: 'Cost Data',
    placeholder: '{\n  "tuition_annual": null,\n  "fees": {"university_fee": 3300, "health_fee": 1400},\n  "total_cost_attendance": 84374,\n  "source": "College Scorecard"\n}',
    hint: 'JSON dict. Surfaces on the Costs & Aid tab. Include source for annotation.',
  },
  {
    key: 'outcomes_data',
    label: 'Outcomes Data',
    placeholder: '{\n  "cip_code": "52.0301",\n  "earnings_1yr_median": 77828,\n  "earnings_4yr_median": 137804,\n  "source": "College Scorecard"\n}',
    hint: 'JSON dict. Supports earnings_1yr_median / earnings_4yr_median for the Outcomes tab.',
  },
]

function parseJsonSafe(text: string): unknown | undefined {
  if (!text || !text.trim()) return undefined
  return JSON.parse(text)
}

export default function ProgramEditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = !!id

  const programQ = useQuery({
    queryKey: ['institution-program', id],
    queryFn: () => getInstitutionProgram(id!),
    enabled: isEdit,
  })

  const form = useForm<FormData>({
    resolver: zodResolver(schema) as any,
    defaultValues: {
      tracks_concentrations: [{ value: '' }],
      tracks_note: '',
      highlights: [{ value: '' }],
      media_urls: [{ value: '' }],
      requirements: [{ key: '', value: '' }],
      faculty_contacts: [],
    },
  })

  const tracksField = useFieldArray({ control: form.control, name: 'tracks_concentrations' })
  const highlightsField = useFieldArray({ control: form.control, name: 'highlights' })
  const mediaField = useFieldArray({ control: form.control, name: 'media_urls' })
  const requirementsField = useFieldArray({ control: form.control, name: 'requirements' })
  const facultyField = useFieldArray({ control: form.control, name: 'faculty_contacts' })

  // JSON field state (kept outside react-hook-form because zod-schema coupling
  // to unstructured JSONB is fragile; we validate on submit).
  const [jsonText, setJsonText] = useState<Record<JsonFieldKey, string>>({
    application_requirements: '',
    intake_rounds: '',
    cost_data: '',
    outcomes_data: '',
  })
  const [jsonErrors, setJsonErrors] = useState<Partial<Record<JsonFieldKey, string>>>({})

  useEffect(() => {
    if (programQ.data) {
      const p = programQ.data
      // tracks in DB is a dict (e.g., {concentrations: [...], note: "..."}).
      // Legacy seeds may be a plain string[] — coerce either shape into the
      // concentrations + note form.
      let tracksConcentrations: string[] = []
      let tracksNote = ''
      const rawTracks = p.tracks
      if (Array.isArray(rawTracks)) {
        tracksConcentrations = rawTracks as string[]
      } else if (rawTracks && typeof rawTracks === 'object') {
        tracksConcentrations = Array.isArray((rawTracks as any).concentrations)
          ? (rawTracks as any).concentrations
          : []
        tracksNote = (rawTracks as any).note ?? ''
      }

      form.reset({
        program_name: p.program_name,
        degree_type: p.degree_type,
        department: p.department ?? '',
        duration_months: p.duration_months ?? undefined,
        tuition: p.tuition ?? undefined,
        acceptance_rate: p.acceptance_rate ?? undefined,
        delivery_format: p.delivery_format ?? '',
        campus_setting: p.campus_setting ?? '',
        application_deadline: p.application_deadline?.split('T')[0] ?? '',
        program_start_date: p.program_start_date?.split('T')[0] ?? '',
        description_text: p.description_text ?? '',
        who_its_for: p.who_its_for ?? '',
        tracks_concentrations: tracksConcentrations.length
          ? tracksConcentrations.map(t => ({ value: t }))
          : [{ value: '' }],
        tracks_note: tracksNote,
        highlights: p.highlights?.length ? p.highlights.map(h => ({ value: h })) : [{ value: '' }],
        media_urls: p.media_urls?.length ? p.media_urls.map(m => ({ value: m })) : [{ value: '' }],
        requirements: p.requirements
          ? Object.entries(p.requirements).map(([key, value]) => ({ key, value: String(value) }))
          : [{ key: '', value: '' }],
        faculty_contacts: (p.faculty_contacts as any[]) ?? [],
      })

      setJsonText({
        application_requirements: p.application_requirements
          ? JSON.stringify(p.application_requirements, null, 2)
          : '',
        intake_rounds: p.intake_rounds ? JSON.stringify(p.intake_rounds, null, 2) : '',
        cost_data: p.cost_data ? JSON.stringify(p.cost_data, null, 2) : '',
        outcomes_data: p.outcomes_data ? JSON.stringify(p.outcomes_data, null, 2) : '',
      })
    }
  }, [programQ.data, form])

  const buildPayload = (data: FormData) => {
    // Parse JSON fields up-front so validation errors surface before mutation.
    const parsedJson: Partial<Record<JsonFieldKey, unknown>> = {}
    const newErrors: Partial<Record<JsonFieldKey, string>> = {}
    for (const { key } of JSON_FIELDS) {
      try {
        parsedJson[key] = parseJsonSafe(jsonText[key])
      } catch (e: any) {
        newErrors[key] = `Invalid JSON: ${e?.message || 'parse error'}`
      }
    }
    if (Object.keys(newErrors).length) {
      setJsonErrors(newErrors)
      throw new Error('JSON validation failed')
    }
    setJsonErrors({})

    // tracks: emit dict with concentrations + optional note (matches NYU shape).
    const concentrations = (data.tracks_concentrations ?? [])
      .map(t => t.value)
      .filter(Boolean)
    const tracks = concentrations.length || (data.tracks_note ?? '').trim()
      ? { concentrations, ...(data.tracks_note?.trim() ? { note: data.tracks_note.trim() } : {}) }
      : undefined

    return {
      program_name: data.program_name,
      degree_type: data.degree_type,
      department: data.department || undefined,
      duration_months: data.duration_months ?? undefined,
      tuition: data.tuition ?? undefined,
      acceptance_rate: data.acceptance_rate ?? undefined,
      delivery_format: data.delivery_format || undefined,
      campus_setting: data.campus_setting || undefined,
      application_deadline: data.application_deadline || undefined,
      program_start_date: data.program_start_date || undefined,
      description_text: data.description_text || undefined,
      who_its_for: data.who_its_for || undefined,
      tracks,
      highlights: data.highlights?.map(h => h.value).filter(Boolean) || undefined,
      media_urls: data.media_urls?.map(m => m.value).filter(Boolean) || undefined,
      requirements: data.requirements?.reduce((acc, r) => {
        if (r.key) acc[r.key] = r.value
        return acc
      }, {} as Record<string, any>) || undefined,
      faculty_contacts: data.faculty_contacts?.filter(f => f.name) || undefined,
      application_requirements: parsedJson.application_requirements as any,
      intake_rounds: parsedJson.intake_rounds as any,
      cost_data: parsedJson.cost_data as any,
      outcomes_data: parsedJson.outcomes_data as any,
    }
  }

  const createMut = useMutation({
    mutationFn: createProgram,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program created', 'success')
      navigate(`/i/programs/${data.id}/edit`)
    },
    onError: () => showToast('Failed to create program', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: (payload: any) => updateProgram(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      queryClient.invalidateQueries({ queryKey: ['institution-program', id] })
      showToast('Program updated', 'success')
    },
    onError: () => showToast('Failed to update program', 'error'),
  })

  const publishMut = useMutation({
    mutationFn: publishProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      queryClient.invalidateQueries({ queryKey: ['institution-program', id] })
      showToast('Program published!', 'success')
    },
    onError: () => showToast('Failed to publish', 'error'),
  })

  const onSaveDraft = form.handleSubmit(
    (data: FormData) => {
      try {
        const payload = buildPayload(data)
        if (isEdit) updateMut.mutate(payload)
        else createMut.mutate(payload)
      } catch {
        showToast('Please fix JSON errors before saving', 'error')
      }
    },
    () => {
      showToast('Please complete required fields before saving', 'warning')
    },
  )

  const onSaveAndPublish = form.handleSubmit(
    async (data: FormData) => {
      try {
        const payload = buildPayload(data)
        if (isEdit) {
          await updateMut.mutateAsync(payload)
          publishMut.mutate(id!)
        } else {
          const created = await createMut.mutateAsync(payload)
          publishMut.mutate(created.id)
        }
      } catch {
        showToast('Please fix JSON errors before publishing', 'error')
      }
    },
    () => {
      showToast('Please complete required fields before publishing', 'warning')
    },
  )

  const saving = createMut.isPending || updateMut.isPending || publishMut.isPending

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{isEdit ? 'Edit Program' : 'New Program'}</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onSaveDraft} disabled={saving} className="flex items-center gap-2">
            <Save size={16} /> Save as Draft
          </Button>
          <Button onClick={onSaveAndPublish} disabled={saving} className="flex items-center gap-2">
            <Send size={16} /> Save & Publish
          </Button>
        </div>
      </div>

      {/* Details */}
      <Card className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Details</h2>
        <Input label="Program Name *" {...form.register('program_name')} error={form.formState.errors.program_name?.message} />
        <div className="grid grid-cols-2 gap-4">
          <Select label="Degree Type *" options={DEGREE_OPTIONS} placeholder="Select" {...form.register('degree_type')} error={form.formState.errors.degree_type?.message} />
          <Input label="Department" {...form.register('department')} />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Input label="Duration (months)" type="number" {...form.register('duration_months')} />
          <Input label="Tuition (USD)" type="number" {...form.register('tuition')} />
          <Input label="Acceptance Rate (0-1)" type="number" step="0.01" {...form.register('acceptance_rate')} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Select label="Delivery Format" options={DELIVERY_FORMAT_OPTIONS} {...form.register('delivery_format')} />
          <Select label="Campus Setting" options={CAMPUS_SETTING_OPTIONS} {...form.register('campus_setting')} />
        </div>
      </Card>

      {/* Dates */}
      <Card className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Dates</h2>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Application Deadline" type="date" {...form.register('application_deadline')} />
          <Input label="Program Start Date" type="date" {...form.register('program_start_date')} />
        </div>
      </Card>

      {/* Description */}
      <Card className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Description</h2>
        <Textarea {...form.register('description_text')} rows={5} placeholder="Describe your program..." />
        <Textarea label="Who it's for" {...form.register('who_its_for')} rows={3} placeholder="Describe the ideal student for this program..." />
      </Card>

      {/* Media URLs */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Media URLs</h2>
            <p className="text-xs text-gray-500">S3 URLs used as the program hero/gallery. First entry is the card image.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => mediaField.append({ value: '' })} className="flex items-center gap-1">
            <Plus size={14} /> Add
          </Button>
        </div>
        {mediaField.fields.map((field, i) => (
          <div key={field.id} className="flex items-center gap-2">
            <Input className="flex-1" {...form.register(`media_urls.${i}.value`)} placeholder="https://unipaith-documents.s3.amazonaws.com/catalog/..." />
            <button type="button" onClick={() => mediaField.remove(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        ))}
      </Card>

      {/* Tracks / Concentrations */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Tracks / Concentrations</h2>
            <p className="text-xs text-gray-500">Stored as {'{ concentrations: string[], note?: string }'} — matches the NYU bulletin shape.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => tracksField.append({ value: '' })} className="flex items-center gap-1">
            <Plus size={14} /> Add
          </Button>
        </div>
        {tracksField.fields.map((field, i) => (
          <div key={field.id} className="flex items-center gap-2">
            <Input className="flex-1" {...form.register(`tracks_concentrations.${i}.value`)} placeholder="e.g. Artificial Intelligence" />
            <button type="button" onClick={() => tracksField.remove(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        ))}
        <Textarea
          label="Note (optional)"
          {...form.register('tracks_note')}
          rows={2}
          placeholder='e.g. "Single BS in Business with 13 concentration options"'
        />
      </Card>

      {/* Highlights */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Highlights</h2>
          <Button variant="ghost" size="sm" onClick={() => highlightsField.append({ value: '' })} className="flex items-center gap-1">
            <Plus size={14} /> Add
          </Button>
        </div>
        {highlightsField.fields.map((field, i) => (
          <div key={field.id} className="flex items-center gap-2">
            <Input className="flex-1" {...form.register(`highlights.${i}.value`)} placeholder="e.g. Top 10 program nationally" />
            <button type="button" onClick={() => highlightsField.remove(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        ))}
      </Card>

      {/* Academic Requirements (structured key-value dict) */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Academic Requirements</h2>
            <p className="text-xs text-gray-500">Key/value pairs (e.g. min_gpa, languages). Distinct from the application checklist below.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => requirementsField.append({ key: '', value: '' })} className="flex items-center gap-1">
            <Plus size={14} /> Add
          </Button>
        </div>
        {requirementsField.fields.map((field, i) => (
          <div key={field.id} className="flex items-center gap-2">
            <Input className="w-40" {...form.register(`requirements.${i}.key`)} placeholder="Key" />
            <Input className="flex-1" {...form.register(`requirements.${i}.value`)} placeholder="Value" />
            <button type="button" onClick={() => requirementsField.remove(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        ))}
      </Card>

      {/* Faculty Contacts */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Faculty Contacts</h2>
          <Button variant="ghost" size="sm" onClick={() => facultyField.append({ name: '', email: '', role: '' })} className="flex items-center gap-1">
            <Plus size={14} /> Add
          </Button>
        </div>
        {facultyField.fields.map((field, i) => (
          <div key={field.id} className="flex items-center gap-2">
            <Input className="flex-1" {...form.register(`faculty_contacts.${i}.name`)} placeholder="Name" />
            <Input className="flex-1" {...form.register(`faculty_contacts.${i}.email`)} placeholder="Email" />
            <Input className="w-32" {...form.register(`faculty_contacts.${i}.role`)} placeholder="Role" />
            <button type="button" onClick={() => facultyField.remove(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        ))}
      </Card>

      {/* Structured JSONB fields (application_requirements, intake_rounds, cost_data, outcomes_data) */}
      {JSON_FIELDS.map(({ key, label, placeholder, hint }) => (
        <Card key={key} className="p-6 space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{label}</h2>
            <p className="text-xs text-gray-500">{hint}</p>
          </div>
          <textarea
            className="w-full rounded border border-gray-300 p-3 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-400"
            rows={6}
            value={jsonText[key]}
            placeholder={placeholder}
            onChange={e => setJsonText(prev => ({ ...prev, [key]: e.target.value }))}
          />
          {jsonErrors[key] && <p className="text-xs text-red-600">{jsonErrors[key]}</p>}
        </Card>
      ))}
    </div>
  )
}
