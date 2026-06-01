import { useEffect, useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Building2, BookOpen, Database, Users, Check, ArrowLeft, ArrowRight,
  ExternalLink, Mail, UserPlus, PartyPopper,
} from 'lucide-react'
import {
  completeInstitutionSetup,
  createInstitution,
  createProgram,
  getInstitution,
  getInstitutionSetup,
  patchInstitutionSetupStep,
  updateInstitution,
} from '../../api/institutions'
import { inviteTeamMember } from '../../api/settings'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Wordmark from '../../components/ui/Wordmark'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { INSTITUTION_TYPES } from '../../utils/constants'

const STEP_META = [
  { label: 'Profile', icon: Building2 },
  { label: 'Program', icon: BookOpen },
  { label: 'Data', icon: Database },
  { label: 'Invite team', icon: Users },
]

const DEGREE_OPTIONS = [
  { value: 'bachelors', label: "Bachelor's" },
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'Ph.D.' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'diploma', label: 'Diploma' },
]

const MODALITY_OPTIONS = [
  { value: 'in_person', label: 'In person' },
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
]

const TEAM_ROLES = [
  { value: 'admissions', label: 'Admissions' },
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'it', label: 'IT' },
]

const institutionSchema = z.object({
  name: z.string().min(1, 'Required'),
  type: z.string().min(1, 'Required'),
  country: z.string().min(1, 'Required'),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url('Enter a valid URL').optional().or(z.literal('')),
  description_text: z.string().optional(),
})
type InstitutionForm = z.infer<typeof institutionSchema>

const programSchema = z.object({
  program_name: z.string().min(1, 'Required'),
  degree_type: z.string().min(1, 'Required'),
  delivery_format: z.string().min(1, 'Required'),
  application_deadline: z.string().optional(),
  tuition: z.coerce.number().optional(),
  requirements_summary: z.string().optional(),
})
type ProgramForm = z.infer<typeof programSchema>

function SetupProgressRail({ currentStep, stepsComplete }: { currentStep: number; stepsComplete: Record<string, boolean> }) {
  return (
    <div className="flex items-center justify-center gap-1 sm:gap-2" aria-label="Setup progress">
      {STEP_META.map((step, i) => {
        const stepNum = i + 1
        const done = stepsComplete[['profile', 'program', 'data', 'team'][i]] || stepNum < currentStep
        const active = stepNum === currentStep
        return (
          <div key={step.label} className="flex items-center gap-1 sm:gap-2">
            <div className="flex flex-col items-center gap-1 min-w-[3.5rem] sm:min-w-[4.5rem]">
              <div
                className={`w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center text-xs sm:text-sm font-medium transition-colors ${
                  done
                    ? 'bg-secondary text-secondary-foreground'
                    : active
                      ? 'bg-secondary/15 text-secondary ring-2 ring-secondary'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {done && !active ? <Check size={14} /> : stepNum}
              </div>
              <span className={`text-[10px] sm:text-xs text-center leading-tight ${active ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {step.label}
              </span>
            </div>
            {i < STEP_META.length - 1 && (
              <div
                className={`hidden sm:block w-8 lg:w-12 h-0.5 mb-4 ${stepNum < currentStep || done ? 'bg-secondary' : 'bg-border'}`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

function SetupCompleteSummary() {
  return (
    <Card className="p-8">
      <div className="text-center mb-6">
        <PartyPopper size={40} className="mx-auto text-primary mb-3" />
        <h2 className="text-xl font-semibold text-foreground">Setup complete</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Your institution profile and first program are in place. Edit details any time.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Link to="/i/settings" className="flex items-center justify-between rounded-lg border border-border px-4 py-3 hover:bg-muted transition-colors">
          <span className="text-sm font-medium">Edit in Settings</span>
          <ExternalLink size={14} className="text-muted-foreground" />
        </Link>
        <Link to="/i/programs" className="flex items-center justify-between rounded-lg border border-border px-4 py-3 hover:bg-muted transition-colors">
          <span className="text-sm font-medium">Manage Programs</span>
          <ExternalLink size={14} className="text-muted-foreground" />
        </Link>
        <Link to="/i/data" className="flex items-center justify-between rounded-lg border border-border px-4 py-3 hover:bg-muted transition-colors">
          <span className="text-sm font-medium">Upload data</span>
          <ExternalLink size={14} className="text-muted-foreground" />
        </Link>
        <Link to="/i/dashboard" className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 hover:bg-primary/10 transition-colors">
          <span className="text-sm font-medium text-foreground">Go to Dashboard</span>
          <ArrowRight size={14} className="text-primary" />
        </Link>
      </div>
    </Card>
  )
}

export default function SetupPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [teamEmail, setTeamEmail] = useState('')
  const [teamRole, setTeamRole] = useState('admissions')

  const setupQ = useQuery({ queryKey: ['institution-setup'], queryFn: getInstitutionSetup })
  const institutionQ = useQuery({
    queryKey: ['institution'],
    queryFn: getInstitution,
    retry: false,
    enabled: !!setupQ.data?.institution_id,
  })

  const currentStep = setupQ.data?.step ?? 1
  const stepsComplete = setupQ.data?.steps_complete ?? {
    profile: false, program: false, data: false, team: false,
  }

  const instForm = useForm<InstitutionForm>({ resolver: zodResolver(institutionSchema) })
  const progForm = useForm<ProgramForm>({
    resolver: zodResolver(programSchema) as any,
    defaultValues: { delivery_format: 'hybrid' },
  })

  useEffect(() => {
    if (!institutionQ.data) return
    instForm.reset({
      name: institutionQ.data.name,
      type: institutionQ.data.type,
      country: institutionQ.data.country,
      region: institutionQ.data.region ?? '',
      city: institutionQ.data.city ?? '',
      website_url: institutionQ.data.website_url ?? '',
      description_text: institutionQ.data.description_text ?? '',
    })
  }, [institutionQ.data, instForm])

  const invalidateSetup = () => {
    queryClient.invalidateQueries({ queryKey: ['institution-setup'] })
    queryClient.invalidateQueries({ queryKey: ['institution'] })
  }

  const saveProfileMut = useMutation({
    mutationFn: async (data: InstitutionForm) => {
      const payload = {
        name: data.name,
        type: data.type,
        country: data.country,
        region: data.region || undefined,
        city: data.city || undefined,
        website_url: data.website_url || undefined,
        description_text: data.description_text || undefined,
      }
      if (setupQ.data?.institution_id) {
        await updateInstitution(payload)
      } else {
        await createInstitution(payload)
      }
      await patchInstitutionSetupStep({ step: 2 })
    },
    onSuccess: () => {
      invalidateSetup()
      showToast('Profile saved', 'success')
    },
    onError: () => showToast('Could not save profile', 'error'),
  })

  const saveProgramMut = useMutation({
    mutationFn: async (data: ProgramForm) => {
      await createProgram({
        program_name: data.program_name,
        degree_type: data.degree_type,
        delivery_format: data.delivery_format,
        application_deadline: data.application_deadline || undefined,
        tuition: data.tuition || undefined,
        description_text: data.requirements_summary || undefined,
        application_requirements: data.requirements_summary
          ? { summary: data.requirements_summary }
          : undefined,
      })
      await patchInstitutionSetupStep({ step: 3 })
    },
    onSuccess: () => {
      invalidateSetup()
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program created — add more details later in Programs', 'success')
    },
    onError: () => showToast('Could not create program', 'error'),
  })

  const advanceStepMut = useMutation({
    mutationFn: (step: number) => patchInstitutionSetupStep({ step }),
    onSuccess: invalidateSetup,
  })

  const finishMut = useMutation({
    mutationFn: completeInstitutionSetup,
    onSuccess: () => {
      invalidateSetup()
      showToast('Setup complete!', 'success')
      navigate('/i/dashboard')
    },
    onError: (e: Error) => showToast(e.message || 'Could not finish setup', 'error'),
  })

  const inviteMut = useMutation({
    mutationFn: () => inviteTeamMember(teamEmail, teamRole),
    onSuccess: () => {
      showToast('Invite sent', 'success')
      setTeamEmail('')
      invalidateSetup()
    },
    onError: (e: Error) => showToast(e.message || 'Could not invite', 'error'),
  })

  const onSubmitProfile = instForm.handleSubmit(
    (data) => saveProfileMut.mutate(data),
    () => showToast('Please complete required fields', 'warning'),
  )

  const onSubmitProgram = progForm.handleSubmit(
    (data) => saveProgramMut.mutate(data),
    () => showToast('Please complete required program fields', 'warning'),
  )

  if (setupQ.isLoading) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-6">
        <Skeleton className="h-8 w-40 mx-auto" />
        <Skeleton className="h-16" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (setupQ.data?.setup_complete) {
    return (
      <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="flex justify-center">
          <Wordmark className="h-7 w-auto" />
        </div>
        <SetupCompleteSummary />
      </div>
    )
  }

  const stickyActions = (content: ReactNode) => (
    <>
      <div className="hidden sm:block">{content}</div>
      <div className="sm:hidden fixed bottom-0 inset-x-0 z-20 border-t border-border bg-background/95 backdrop-blur p-4">
        {content}
      </div>
      <div className="sm:hidden h-20" aria-hidden />
    </>
  )

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-6 pb-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <Wordmark className="h-7 w-auto" />
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-foreground">Set up your institution</h1>
          <p className="text-sm text-muted-foreground mt-1">Step {currentStep} of 4</p>
        </div>
      </div>

      <SetupProgressRail currentStep={currentStep} stepsComplete={stepsComplete} />

      {currentStep === 1 && (
        <Card className="p-5 sm:p-6">
          <h2 className="text-base font-semibold text-foreground mb-1">Institution profile</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Legal name, location, and web presence. Logo uses your wordmark — no decorative imagery.
          </p>
          <form onSubmit={onSubmitProfile} className="space-y-4">
            <Input label="Institution name *" {...instForm.register('name')} error={instForm.formState.errors.name?.message} />
            <Select label="Type *" options={INSTITUTION_TYPES} placeholder="Select type" {...instForm.register('type')} error={instForm.formState.errors.type?.message} />
            <Input label="Country *" {...instForm.register('country')} error={instForm.formState.errors.country?.message} />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Region" {...instForm.register('region')} />
              <Input label="City" {...instForm.register('city')} />
            </div>
            <Input
              label="Primary domain (website)"
              {...instForm.register('website_url')}
              placeholder="https://yourschool.edu"
            />
            <Textarea label="Short description" {...instForm.register('description_text')} rows={3} />
            {stickyActions(
              <div className="flex justify-end">
                <Button type="submit" disabled={saveProfileMut.isPending} className="w-full sm:w-auto">
                  {saveProfileMut.isPending ? 'Saving…' : 'Continue'}
                  <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>,
            )}
          </form>
        </Card>
      )}

      {currentStep === 2 && (
        <Card className="p-5 sm:p-6">
          <h2 className="text-base font-semibold text-foreground mb-1">Add your first program</h2>
          <p className="text-sm text-muted-foreground mb-4">Add more details later in Programs.</p>
          {stepsComplete.program ? (
            <div className="space-y-4">
              <Badge variant="success">First program created</Badge>
              <p className="text-sm text-muted-foreground">You can publish and enrich it from the Programs page after setup.</p>
              {stickyActions(
                <div className="flex flex-col sm:flex-row gap-2 sm:justify-between">
                  <Button type="button" variant="ghost" onClick={() => advanceStepMut.mutate(1)}>
                    <ArrowLeft size={16} className="mr-1" /> Back
                  </Button>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button type="button" variant="secondary" onClick={() => finishMut.mutate()} loading={finishMut.isPending}>
                      Skip to dashboard
                    </Button>
                    <Button type="button" onClick={() => advanceStepMut.mutate(3)}>
                      Continue <ArrowRight size={16} className="ml-1" />
                    </Button>
                  </div>
                </div>,
              )}
            </div>
          ) : (
            <form onSubmit={onSubmitProgram} className="space-y-4">
              <Input label="Program name *" {...progForm.register('program_name')} error={progForm.formState.errors.program_name?.message} />
              <Select label="Degree type *" options={DEGREE_OPTIONS} placeholder="Select degree" {...progForm.register('degree_type')} error={progForm.formState.errors.degree_type?.message} />
              <Select label="Modality *" options={MODALITY_OPTIONS} {...progForm.register('delivery_format')} error={progForm.formState.errors.delivery_format?.message} />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Application deadline" type="date" {...progForm.register('application_deadline')} />
                <Input label="Tuition (USD)" type="number" {...progForm.register('tuition')} />
              </div>
              <Textarea label="Requirements summary" {...progForm.register('requirements_summary')} rows={3} placeholder="GPA, tests, prerequisites…" />
              {stickyActions(
                <div className="flex flex-col sm:flex-row gap-2 sm:justify-between">
                  <Button type="button" variant="ghost" onClick={() => advanceStepMut.mutate(1)}>
                    <ArrowLeft size={16} className="mr-1" /> Back
                  </Button>
                  <div className="flex flex-col sm:flex-row gap-2">
                    {stepsComplete.profile && stepsComplete.program && (
                      <Button type="button" variant="secondary" onClick={() => finishMut.mutate()} loading={finishMut.isPending}>
                        Skip to dashboard
                      </Button>
                    )}
                    <Button type="submit" disabled={saveProgramMut.isPending} className="w-full sm:w-auto">
                      {saveProgramMut.isPending ? 'Creating…' : 'Continue'}
                    </Button>
                  </div>
                </div>,
              )}
            </form>
          )}
        </Card>
      )}

      {currentStep === 3 && (
        <Card className="p-5 sm:p-6">
          <h2 className="text-base font-semibold text-foreground mb-1">Upload data</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Upload admissions history or a prospect list to power analytics and matching.
          </p>
          <div className="rounded-lg border border-dashed border-border bg-muted/30 p-6 text-center mb-4">
            <Database size={32} className="mx-auto text-secondary mb-2" />
            <p className="text-sm text-muted-foreground mb-4">
              Datasets help segmentation, campaigns, and match quality. This step is optional.
            </p>
            <Button variant="secondary" onClick={() => navigate('/i/data')}>
              Open data upload <ExternalLink size={14} className="ml-1" />
            </Button>
          </div>
          {stickyActions(
            <div className="flex flex-col sm:flex-row gap-2 sm:justify-between">
              <Button type="button" variant="ghost" onClick={() => advanceStepMut.mutate(2)}>
                <ArrowLeft size={16} className="mr-1" /> Back
              </Button>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button type="button" variant="secondary" onClick={() => advanceStepMut.mutate(4)}>
                  I&apos;ll do this later
                </Button>
                <Button type="button" onClick={() => advanceStepMut.mutate(4)}>
                  Continue <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>
            </div>,
          )}
        </Card>
      )}

      {currentStep === 4 && (
        <Card className="p-5 sm:p-6">
          <h2 className="text-base font-semibold text-foreground mb-1">Invite your team</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Invite colleagues with roles. Each invite is audit-logged. Optional — skip if you&apos;re solo for now.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end mb-4">
            <div className="flex-1">
              <Input
                label="Email"
                type="email"
                value={teamEmail}
                onChange={e => setTeamEmail(e.target.value)}
                placeholder="colleague@school.edu"
                leftIcon={<Mail size={15} />}
              />
            </div>
            <div className="w-full sm:w-44">
              <Select label="Role" options={TEAM_ROLES} value={teamRole} onChange={e => setTeamRole(e.target.value)} />
            </div>
            <div className="pb-[26px]">
              <Button variant="secondary" disabled={!teamEmail || inviteMut.isPending} loading={inviteMut.isPending} onClick={() => inviteMut.mutate()}>
                <UserPlus size={15} className="mr-1" /> Invite
              </Button>
            </div>
          </div>
          {stickyActions(
            <div className="flex flex-col sm:flex-row gap-2 sm:justify-between">
              <Button type="button" variant="ghost" onClick={() => advanceStepMut.mutate(3)}>
                <ArrowLeft size={16} className="mr-1" /> Back
              </Button>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button type="button" variant="secondary" onClick={() => finishMut.mutate()} loading={finishMut.isPending}>
                  Skip to dashboard
                </Button>
                <Button type="button" onClick={() => finishMut.mutate()} loading={finishMut.isPending} className="bg-primary text-primary-foreground hover:brightness-95">
                  Finish setup
                </Button>
              </div>
            </div>,
          )}
        </Card>
      )}
    </div>
  )
}
