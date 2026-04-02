import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Building2, BookOpen, ClipboardList, PartyPopper, Plus, Trash2 } from 'lucide-react'
import { createInstitution, createProgram } from '../../api/institutions'
import { createRubric } from '../../api/reviews'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import { showToast } from '../../stores/toast-store'
import { INSTITUTION_TYPES } from '../../utils/constants'

const institutionSchema = z.object({
  name: z.string().min(1, 'Required'),
  type: z.string().min(1, 'Required'),
  country: z.string().min(1, 'Required'),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal('')),
  description_text: z.string().optional(),
})
type InstitutionForm = z.infer<typeof institutionSchema>

const programSchema = z.object({
  program_name: z.string().min(1, 'Required'),
  degree_type: z.string().min(1, 'Required'),
  department: z.string().optional(),
  duration_months: z.coerce.number().optional(),
  tuition: z.coerce.number().optional(),
  application_deadline: z.string().optional(),
  program_start_date: z.string().optional(),
  description_text: z.string().optional(),
})
type ProgramForm = z.infer<typeof programSchema>

const STEPS = [
  { label: 'Institution', icon: Building2 },
  { label: 'Program', icon: BookOpen },
  { label: 'Rubric', icon: ClipboardList },
  { label: 'Done', icon: PartyPopper },
]

const DEGREE_OPTIONS = [
  { value: 'bachelors', label: "Bachelor's" },
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'Ph.D.' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'diploma', label: 'Diploma' },
]

export default function SetupPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [currentStep, setCurrentStep] = useState(0)
  const [, setCreatedInstitutionId] = useState<string | null>(null)
  const [createdProgramId, setCreatedProgramId] = useState<string | null>(null)

  // Rubric state
  const [rubricName, setRubricName] = useState('')
  const [criteria, setCriteria] = useState<{ name: string; weight: number }[]>([
    { name: 'Academic Performance', weight: 30 },
    { name: 'Test Scores', weight: 20 },
    { name: 'Extracurriculars', weight: 20 },
    { name: 'Essay Quality', weight: 15 },
    { name: 'Recommendations', weight: 15 },
  ])

  const instForm = useForm<InstitutionForm>({ resolver: zodResolver(institutionSchema) })
  const progForm = useForm<ProgramForm>({ resolver: zodResolver(programSchema) as any })

  const createInstMut = useMutation({
    mutationFn: createInstitution,
    onSuccess: (data) => {
      setCreatedInstitutionId(data.id)
      queryClient.invalidateQueries({ queryKey: ['institution'] })
      showToast('Institution created!', 'success')
      setCurrentStep(1)
    },
    onError: () => showToast('Failed to create institution', 'error'),
  })

  const createProgMut = useMutation({
    mutationFn: createProgram,
    onSuccess: (data) => {
      setCreatedProgramId(data.id)
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program created!', 'success')
      setCurrentStep(2)
    },
    onError: () => showToast('Failed to create program', 'error'),
  })

  const createRubricMut = useMutation({
    mutationFn: createRubric,
    onSuccess: () => {
      showToast('Rubric created!', 'success')
      setCurrentStep(3)
    },
    onError: () => showToast('Failed to create rubric', 'error'),
  })

  const onSubmitInstitution = instForm.handleSubmit(
    (data) => {
      createInstMut.mutate({
        name: data.name,
        type: data.type,
        country: data.country,
        region: data.region || undefined,
        city: data.city || undefined,
        website_url: data.website_url || undefined,
        description_text: data.description_text || undefined,
      })
    },
    () => {
      showToast('Please complete required institution fields', 'warning')
    },
  )

  const onSubmitProgram = progForm.handleSubmit(
    (data) => {
      createProgMut.mutate({
        program_name: data.program_name,
        degree_type: data.degree_type,
        department: data.department || undefined,
        duration_months: data.duration_months || undefined,
        tuition: data.tuition || undefined,
        application_deadline: data.application_deadline || undefined,
        program_start_date: data.program_start_date || undefined,
        description_text: data.description_text || undefined,
      })
    },
    () => {
      showToast('Please complete required program fields', 'warning')
    },
  )

  const onSubmitRubric = () => {
    const total = criteria.reduce((s, c) => s + c.weight, 0)
    if (total !== 100) {
      showToast(`Weights must sum to 100 (currently ${total})`, 'warning')
      return
    }
    createRubricMut.mutate({
      rubric_name: rubricName || 'Default Rubric',
      criteria,
      program_id: createdProgramId,
    })
  }

  const addCriterion = () => setCriteria([...criteria, { name: '', weight: 0 }])
  const removeCriterion = (i: number) => setCriteria(criteria.filter((_, idx) => idx !== i))
  const updateCriterion = (i: number, field: 'name' | 'weight', value: string | number) => {
    setCriteria(criteria.map((c, idx) => idx === i ? { ...c, [field]: value } : c))
  }

  const weightSum = criteria.reduce((s, c) => s + c.weight, 0)

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2">
        {STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center gap-2">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                i < currentStep
                  ? 'bg-indigo-600 text-white'
                  : i === currentStep
                  ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-600'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {i < currentStep ? <Check size={16} /> : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`w-12 h-0.5 ${i < currentStep ? 'bg-indigo-600' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900">{STEPS[currentStep].label}</h2>
      </div>

      {/* Step 1: Institution */}
      {currentStep === 0 && (
        <Card className="p-6">
          <form onSubmit={onSubmitInstitution} className="space-y-4">
            <Input label="Institution Name *" {...instForm.register('name')} error={instForm.formState.errors.name?.message} />
            <Select label="Type *" options={INSTITUTION_TYPES} placeholder="Select type" {...instForm.register('type')} error={instForm.formState.errors.type?.message} />
            <Input label="Country *" {...instForm.register('country')} error={instForm.formState.errors.country?.message} />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Region" {...instForm.register('region')} />
              <Input label="City" {...instForm.register('city')} />
            </div>
            <Input label="Website URL" {...instForm.register('website_url')} placeholder="https://..." />
            <Textarea label="Description" {...instForm.register('description_text')} rows={3} />
            <div className="flex justify-end">
              <Button type="submit" disabled={createInstMut.isPending}>
                {createInstMut.isPending ? 'Creating...' : 'Next'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Step 2: Program */}
      {currentStep === 1 && (
        <Card className="p-6">
          <form onSubmit={onSubmitProgram} className="space-y-4">
            <Input label="Program Name *" {...progForm.register('program_name')} error={progForm.formState.errors.program_name?.message} />
            <Select label="Degree Type *" options={DEGREE_OPTIONS} placeholder="Select degree" {...progForm.register('degree_type')} error={progForm.formState.errors.degree_type?.message} />
            <Input label="Department" {...progForm.register('department')} />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Duration (months)" type="number" {...progForm.register('duration_months')} />
              <Input label="Tuition (USD)" type="number" {...progForm.register('tuition')} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Application Deadline" type="date" {...progForm.register('application_deadline')} />
              <Input label="Start Date" type="date" {...progForm.register('program_start_date')} />
            </div>
            <Textarea label="Description" {...progForm.register('description_text')} rows={3} />
            <div className="flex justify-between">
              <Button type="button" variant="ghost" onClick={() => setCurrentStep(0)}>Back</Button>
              <Button type="submit" disabled={createProgMut.isPending}>
                {createProgMut.isPending ? 'Creating...' : 'Next'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Step 3: Rubric (optional) */}
      {currentStep === 2 && (
        <Card className="p-6">
          <p className="text-sm text-gray-500 mb-4">Optionally create a rubric to score applications. You can skip and do this later.</p>
          <div className="space-y-4">
            <Input label="Rubric Name" value={rubricName} onChange={e => setRubricName(e.target.value)} placeholder="e.g. Default Rubric" />
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">Criteria</label>
                <span className={`text-xs font-medium ${weightSum === 100 ? 'text-green-600' : 'text-red-600'}`}>
                  Total: {weightSum}/100
                </span>
              </div>
              <div className="space-y-2">
                {criteria.map((c, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Input
                      className="flex-1"
                      placeholder="Criterion name"
                      value={c.name}
                      onChange={e => updateCriterion(i, 'name', e.target.value)}
                    />
                    <Input
                      className="w-20"
                      type="number"
                      value={c.weight}
                      onChange={e => updateCriterion(i, 'weight', Number(e.target.value))}
                    />
                    <button type="button" onClick={() => removeCriterion(i)} className="p-1 text-gray-400 hover:text-red-500">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={addCriterion} className="mt-2 flex items-center gap-1">
                <Plus size={14} /> Add Criterion
              </Button>
            </div>
            <div className="flex justify-between">
              <Button type="button" variant="ghost" onClick={() => setCurrentStep(1)}>Back</Button>
              <div className="flex gap-2">
                <Button type="button" variant="secondary" onClick={() => setCurrentStep(3)}>Skip</Button>
                <Button type="button" onClick={onSubmitRubric} disabled={createRubricMut.isPending}>
                  {createRubricMut.isPending ? 'Creating...' : 'Create Rubric'}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Step 4: Done */}
      {currentStep === 3 && (
        <Card className="p-8 text-center">
          <PartyPopper size={48} className="mx-auto text-indigo-500 mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">You're all set!</h3>
          <p className="text-gray-600 mb-6">Your institution and first program are ready. You can now manage programs, review applications, and more.</p>
          <div className="flex justify-center gap-3">
            <Button onClick={() => navigate('/i')}>Go to Dashboard</Button>
            <Button variant="secondary" onClick={() => navigate('/i/programs')}>Manage Programs</Button>
          </div>
        </Card>
      )}
    </div>
  )
}
