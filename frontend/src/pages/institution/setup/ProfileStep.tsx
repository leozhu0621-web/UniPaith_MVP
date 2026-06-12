import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { createInstitution, updateInstitution, draftCampaignCopy } from '../../../api/institutions'
import type { Institution } from '../../../types'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Wordmark from '../../../components/ui/Wordmark'
import { showToast } from '../../../stores/toast-store'
import { INSTITUTION_TYPES } from '../../../utils/constants'
import WizardFooter from './WizardFooter'

const schema = z.object({
  name: z.string().min(1, 'Required'),
  type: z.string().min(1, 'Required'),
  country: z.string().min(1, 'Required'),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url('Enter a valid URL (https://…)').optional().or(z.literal('')),
  description_text: z.string().min(1, 'A short description makes your profile publishable'),
})
type ProfileForm = z.infer<typeof schema>

export default function ProfileStep({
  institution,
  onSaved,
}: {
  institution: Institution | null
  onSaved: () => void
}) {
  const queryClient = useQueryClient()
  const [drafting, setDrafting] = useState(false)

  const form = useForm<ProfileForm>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: institution?.name ?? '',
      type: institution?.type ?? '',
      country: institution?.country ?? '',
      region: institution?.region ?? '',
      city: institution?.city ?? '',
      website_url: institution?.website_url ?? '',
      description_text: institution?.description_text ?? '',
    },
  })

  const watchedName = form.watch('name')

  const save = useMutation({
    mutationFn: async (data: ProfileForm) => {
      const payload = {
        name: data.name,
        type: data.type,
        country: data.country,
        region: data.region || undefined,
        city: data.city || undefined,
        website_url: data.website_url || undefined,
        description_text: data.description_text || undefined,
      }
      return institution ? updateInstitution(payload) : createInstitution(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution'] })
      queryClient.invalidateQueries({ queryKey: ['institution-setup'] })
      onSaved()
    },
    onError: () => showToast('Could not save your profile. Please try again.', 'error'),
  })

  // Spec 30 §7 — optional AI draft of the description; the admin edits before saving.
  const draftDescription = async () => {
    const name = form.getValues('name')
    const type = form.getValues('type')
    if (!name) {
      showToast('Add your institution name first', 'warning')
      return
    }
    setDrafting(true)
    try {
      const copy = await draftCampaignCopy({
        objective: 'awareness',
        tone: 'editorial',
        audience_summary: 'prospective students discovering this institution',
        additional_context: `Write a concise 2–3 sentence institution description for "${name}"${type ? ` (a ${type})` : ''}. Plain, editorial tone — no marketing hype.`,
      })
      if (copy?.body) {
        form.setValue('description_text', copy.body.trim(), { shouldValidate: true })
        showToast('Draft added — edit it to match your voice', 'success')
      } else {
        showToast('No draft returned — write your own below', 'info')
      }
    } catch {
      showToast('AI draft is unavailable right now — write your own below', 'info')
    } finally {
      setDrafting(false)
    }
  }

  const onSubmit = form.handleSubmit(
    (data) => save.mutate(data),
    () => showToast('Please complete the required fields', 'warning'),
  )

  return (
    <Card pad={false} className="p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-foreground">Institution profile</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The basics students see first. You can add more in Settings later.
      </p>

      <form onSubmit={onSubmit} className="mt-5 space-y-4">
        <Input label="Institution name" required {...form.register('name')} error={form.formState.errors.name?.message} />

        {watchedName.trim() && (
          <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2">
            <Wordmark className="h-6 w-auto" />
            <span className="text-xs text-muted-foreground">
              Your wordmark — UniPaith is editorial, so institutions show as a text wordmark, not a logo image.
            </span>
          </div>
        )}

        <Select
          label="Type"
          required
          options={INSTITUTION_TYPES}
          placeholder="Select type"
          {...form.register('type')}
          error={form.formState.errors.type?.message}
        />
        <Input label="Country" required {...form.register('country')} error={form.formState.errors.country?.message} />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Region / State" {...form.register('region')} />
          <Input label="City" {...form.register('city')} />
        </div>
        <Input
          label="Primary domain"
          placeholder="https://www.youruni.edu"
          helperText="Used for your sender identity and trackable links."
          {...form.register('website_url')}
          error={form.formState.errors.website_url?.message}
        />

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="institution-description" className="block text-[13px] font-semibold text-muted-foreground">
              Short description
            </label>
            <button
              type="button"
              onClick={draftDescription}
              disabled={drafting}
              className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:underline disabled:opacity-50"
            >
              <Sparkles size={13} /> {drafting ? 'Drafting…' : 'Draft with AI'}
            </button>
          </div>
          <Textarea
            id="institution-description"
            rows={3}
            placeholder="What makes your institution distinctive — in a couple of plain sentences."
            {...form.register('description_text')}
            error={form.formState.errors.description_text?.message}
          />
        </div>

        <WizardFooter>
          <Button type="submit" variant="secondary" loading={save.isPending}>
            Continue
          </Button>
        </WizardFooter>
      </form>
    </Card>
  )
}
