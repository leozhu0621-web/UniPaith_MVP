import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Building2, BookOpen, ClipboardList, PartyPopper, Plus, Trash2, Search, MapPin, GraduationCap } from 'lucide-react'
import { createInstitution, createProgram, searchUnclaimedInstitutions, claimInstitution } from '../../api/institutions'
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
  const [showManualForm, setShowManualForm] = useState(false)
  const [claimQuery, setClaimQuery] = useState('')
  const [claimResults, setClaimResults] = useState<any[]>([])
  const [claimSearching, setClaimSearching] = useState(false)
  const [, setCreatedInstitutionId] = useState<string | null>(null)
  const [createdProgramId, setCreatedProgramId] = useState<string | null>(null)

  // Debounced search for unclaimed institutions
  useEffect(() => {
    if (claimQuery.length < 2) { setClaimResults([]); return }
    const timer = setTimeout(async () => {
      setClaimSearching(true)
      try {
        const results = await searchUnclaimedInstitutions(claimQuery)
        setClaimResults(results)
      } catch { setClaimResults([]) }
      finally { setClaimSearching(false) }
    }, 400)
    return () => clearTimeout(timer)
  }, [claimQuery])

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

  const claimMut = useMutation({
    mutationFn: (extractedIds: string[]) => claimInstitution(extractedIds),
    onSuccess: (data) => {
      setCreatedInstitutionId(data.id)
      queryClient.invalidateQueries({ queryKey: ['institution'] })
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast(`Claimed ${data.name}! Profile and programs auto-populated.`, 'success')
      setCurrentStep(2) // Skip to Rubric since institution + programs are done
    },
    onError: () => showToast('Failed to claim institution', 'error'),
  })

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
    if (!createdProgramId) {
      showToast('Create or claim a program first before adding a rubric', 'warning')
      return
    }
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
                  ? 'bg-brand-slate-600 text-white'
                  : i === currentStep
                  ? 'bg-brand-slate-100 text-brand-slate-700 ring-2 ring-brand-slate-600'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {i < currentStep ? <Check size={16} /> : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`w-12 h-0.5 ${i < currentStep ? 'bg-brand-slate-600' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900">{STEPS[currentStep].label}</h2>
      </div>

      {/* Step 1: Institution (Claim or Create) */}
      {currentStep === 0 && !showManualForm && (
        <Card className="p-6 space-y-4">
          <div className="text-center">
            <Search size={32} className="mx-auto text-brand-slate-400 mb-2" />
            <h3 className="text-lg font-semibold text-gray-900">Is your institution already in our database?</h3>
            <p className="text-sm text-gray-500 mt-1">Search to claim your school and auto-populate your profile with existing data.</p>
          </div>
          <Input
            label=""
            value={claimQuery}
            onChange={e => setClaimQuery(e.target.value)}
            placeholder="Search by institution name..."
          />
          {claimSearching && <p className="text-sm text-gray-400 text-center">Searching...</p>}
          {claimResults.length > 0 && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {claimResults.map((r: any, i: number) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => claimMut.mutate(r.extracted_ids)}
                  disabled={claimMut.isPending}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-brand-slate-400 hover:bg-brand-slate-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{r.institution_name}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                        {r.institution_city && <span className="flex items-center gap-0.5"><MapPin size={10} /> {r.institution_city}</span>}
                        {r.institution_country && <span>{r.institution_country}</span>}
                        {r.institution_type && <span className="capitalize">{r.institution_type}</span>}
                      </div>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-brand-slate-600 bg-brand-slate-50 px-2 py-1 rounded">
                      <GraduationCap size={12} /> {r.program_count} programs
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
          {claimQuery.length >= 2 && !claimSearching && claimResults.length === 0 && (
            <p className="text-sm text-gray-400 text-center">No matching institutions found.</p>
          )}
          {claimMut.isPending && <p className="text-sm text-brand-slate-600 text-center animate-pulse">Claiming institution and importing programs...</p>}
          <div className="text-center pt-2">
            <button type="button" onClick={() => setShowManualForm(true)} className="text-sm text-brand-slate-600 hover:underline">
              Not listed? Create manually
            </button>
          </div>
        </Card>
      )}

      {currentStep === 0 && showManualForm && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-700">Create Institution Manually</h3>
            <button type="button" onClick={() => setShowManualForm(false)} className="text-xs text-brand-slate-600 hover:underline">Back to search</button>
          </div>
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
          <PartyPopper size={48} className="mx-auto text-brand-slate-500 mb-4" />
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
