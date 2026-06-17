import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createProgram, publishProgram } from '../../../api/institutions'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import { showToast } from '../../../stores/toast-store'
import WizardFooter from './WizardFooter'

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

const schema = z
  .object({
    program_name: z.string().min(1, 'Required'),
    degree_type: z.string().min(1, 'Required'),
    delivery_format: z.string().optional(),
    application_deadline: z.string().optional(),
    program_start_date: z.string().optional(),
    tuition: z.coerce.number().min(0).optional().or(z.nan().transform(() => undefined)),
    description_text: z.string().min(1, 'A short summary is needed to publish'),
  })
  // Publishing needs a cost signal — tuition OR a deadline (Spec 23 §4).
  .refine((d) => d.tuition != null || !!d.application_deadline, {
    message: 'Add tuition or an application deadline',
    path: ['tuition'],
  })
type ProgramForm = z.infer<typeof schema>

export default function ProgramStep({
  onSaved,
  onBack,
}: {
  onSaved: (programId: string) => void
  onBack: () => void
}) {
  const queryClient = useQueryClient()
  const form = useForm<ProgramForm>({ resolver: zodResolver(schema) as never })

  const save = useMutation({
    mutationFn: async (data: ProgramForm) => {
      const program = await createProgram({
        program_name: data.program_name,
        degree_type: data.degree_type as 'bachelors' | 'masters' | 'phd' | 'certificate' | 'diploma',
        delivery_format: (data.delivery_format || undefined) as 'in_person' | 'online' | 'hybrid' | undefined,
        application_deadline: data.application_deadline || undefined,
        program_start_date: data.program_start_date || undefined,
        tuition: data.tuition ?? undefined,
        description_text: data.description_text || undefined,
      })
      // Publish so the institution is matchable (Spec 30 §3.2). If validation
      // fails, the program still exists as a draft — setup can continue.
      let published = false
      try {
        await publishProgram(program.id)
        published = true
      } catch {
        published = false
      }
      return { id: program.id, published }
    },
    onSuccess: ({ id, published }) => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      queryClient.invalidateQueries({ queryKey: ['institution-setup'] })
      showToast(
        published ? 'Program published' : 'Program saved as a draft — publish it later from Programs',
        published ? 'success' : 'info',
      )
      onSaved(id)
    },
    onError: () => showToast('Could not create the program. Please try again.', 'error'),
  })

  const onSubmit = form.handleSubmit(
    (data) => save.mutate(data),
    () => showToast('Please complete the required fields', 'warning'),
  )

  return (
    <Card pad={false} className="p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-foreground">Your first program</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Just the essentials so students can find and match with it. Add more details later.
      </p>

      <form onSubmit={onSubmit} className="mt-5 space-y-4">
        <Input label="Program name" required {...form.register('program_name')} error={form.formState.errors.program_name?.message} />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select
            label="Degree type"
            required
            options={DEGREE_OPTIONS}
            placeholder="Select degree"
            {...form.register('degree_type')}
            error={form.formState.errors.degree_type?.message}
          />
          <Select
            label="Modality"
            options={MODALITY_OPTIONS}
            placeholder="Select modality"
            {...form.register('delivery_format')}
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Application deadline" type="date" {...form.register('application_deadline')} />
          <Input label="Start date" type="date" {...form.register('program_start_date')} />
        </div>
        <Input
          label="Tuition (USD / year)"
          type="number"
          min={0}
          {...form.register('tuition')}
          error={form.formState.errors.tuition?.message}
        />
        <Textarea
          label="Program summary"
          required
          rows={3}
          placeholder="What this program offers and who it's for — a couple of sentences."
          {...form.register('description_text')}
          error={form.formState.errors.description_text?.message}
        />

        <WizardFooter onBack={onBack}>
          <Button type="submit" variant="secondary" loading={save.isPending}>
            Continue
          </Button>
        </WizardFooter>
      </form>
    </Card>
  )
}
