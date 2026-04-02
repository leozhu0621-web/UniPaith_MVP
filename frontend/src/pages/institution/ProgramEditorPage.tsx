import { useEffect } from 'react'
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

const schema = z.object({
  program_name: z.string().min(1, 'Required'),
  degree_type: z.string().min(1, 'Required'),
  department: z.string().optional(),
  duration_months: z.coerce.number().optional(),
  tuition: z.coerce.number().optional(),
  acceptance_rate: z.coerce.number().min(0).max(1).optional(),
  application_deadline: z.string().optional(),
  program_start_date: z.string().optional(),
  description_text: z.string().optional(),
  highlights: z.array(z.object({ value: z.string() })).optional(),
  requirements: z.array(z.object({ key: z.string(), value: z.string() })).optional(),
  faculty_contacts: z.array(z.object({ name: z.string(), email: z.string().optional(), role: z.string().optional() })).optional(),
})
type FormData = z.infer<typeof schema>

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
      highlights: [{ value: '' }],
      requirements: [{ key: '', value: '' }],
      faculty_contacts: [],
    },
  })

  const highlightsField = useFieldArray({ control: form.control, name: 'highlights' })
  const requirementsField = useFieldArray({ control: form.control, name: 'requirements' })
  const facultyField = useFieldArray({ control: form.control, name: 'faculty_contacts' })

  useEffect(() => {
    if (programQ.data) {
      const p = programQ.data
      form.reset({
        program_name: p.program_name,
        degree_type: p.degree_type,
        department: p.department ?? '',
        duration_months: p.duration_months ?? undefined,
        tuition: p.tuition ?? undefined,
        acceptance_rate: p.acceptance_rate ?? undefined,
        application_deadline: p.application_deadline?.split('T')[0] ?? '',
        program_start_date: p.program_start_date?.split('T')[0] ?? '',
        description_text: p.description_text ?? '',
        highlights: p.highlights?.length ? p.highlights.map(h => ({ value: h })) : [{ value: '' }],
        requirements: p.requirements ? Object.entries(p.requirements).map(([key, value]) => ({ key, value: String(value) })) : [{ key: '', value: '' }],
        faculty_contacts: (p.faculty_contacts as any[]) ?? [],
      })
    }
  }, [programQ.data, form])

  const buildPayload = (data: FormData) => ({
    program_name: data.program_name,
    degree_type: data.degree_type,
    department: data.department || undefined,
    duration_months: data.duration_months || undefined,
    tuition: data.tuition || undefined,
    acceptance_rate: data.acceptance_rate || undefined,
    application_deadline: data.application_deadline || undefined,
    program_start_date: data.program_start_date || undefined,
    description_text: data.description_text || undefined,
    highlights: data.highlights?.map(h => h.value).filter(Boolean) || undefined,
    requirements: data.requirements?.reduce((acc, r) => {
      if (r.key) acc[r.key] = r.value
      return acc
    }, {} as Record<string, any>) || undefined,
    faculty_contacts: data.faculty_contacts?.filter(f => f.name) || undefined,
  })

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
      const payload = buildPayload(data)
      if (isEdit) updateMut.mutate(payload)
      else createMut.mutate(payload)
    },
    () => {
      showToast('Please complete required fields before saving', 'warning')
    },
  )

  const onSaveAndPublish = form.handleSubmit(
    async (data: FormData) => {
      const payload = buildPayload(data)
      if (isEdit) {
        await updateMut.mutateAsync(payload)
        publishMut.mutate(id!)
      } else {
        const created = await createMut.mutateAsync(payload)
        publishMut.mutate(created.id)
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

      {/* Requirements */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Requirements</h2>
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
    </div>
  )
}
