import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Plus, Trash2, CreditCard, Users } from 'lucide-react'
import { getInstitution, updateInstitution } from '../../api/institutions'
import { getRubrics, createRubric } from '../../api/reviews'
import { getInstitutionBilling } from '../../api/billing'
import { getInstitutionSettings, updateInstitutionSettings, type UpdateInstitutionSettingsPayload } from '../../api/settings'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { useAuthStore } from '../../stores/auth-store'
import { INSTITUTION_TYPES } from '../../utils/constants'
import { formatDate } from '../../utils/format'
import type { Rubric } from '../../types'
import SecurityCard from '../student/settings/SecurityCard'
import PreferencesCard from '../student/settings/PreferencesCard'
import NotificationsCard from '../student/settings/NotificationsCard'
import TeamCard from './settings/TeamCard'
import IntegrationsCard from './settings/IntegrationsCard'

const CAMPUS_SETTING_OPTIONS = [
  { value: '', label: 'Not specified' },
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
]

const profileSchema = z.object({
  name: z.string().min(1, 'Required'),
  type: z.string().min(1, 'Required'),
  country: z.string().min(1, 'Required'),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal('')),
  contact_email: z.string().email().optional().or(z.literal('')),
  logo_url: z.string().url().optional().or(z.literal('')),
  description_text: z.string().optional(),
  campus_description: z.string().optional(),
  campus_setting: z.string().optional(),
  student_body_size: z.coerce.number().int().nonnegative().optional(),
  founded_year: z.coerce.number().int().nonnegative().optional(),
  media_gallery_text: z.string().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

type InstJsonKey = 'social_links' | 'inquiry_routing' | 'support_services' | 'policies' | 'international_info' | 'school_outcomes'
const INST_JSON_FIELDS: { key: InstJsonKey; label: string; placeholder: string; hint: string }[] = [
  { key: 'social_links', label: 'Social Links', placeholder: '{\n  "twitter": "https://twitter.com/school"\n}', hint: 'JSON dict of platform → URL. Renders on the institution overview.' },
  { key: 'inquiry_routing', label: 'Inquiry Routing', placeholder: '{\n  "general": "admissions@school.edu"\n}', hint: 'JSON dict of inquiry type → destination. Powers the student contact flow.' },
  { key: 'support_services', label: 'Support Services', placeholder: '{\n  "counseling": {"url": "https://…"}\n}', hint: 'JSON dict of service → {url, phone, description}.' },
  { key: 'policies', label: 'Policies', placeholder: '{\n  "transfer_credit": {"url": "https://…"}\n}', hint: 'JSON dict of policy name → {url, summary?}.' },
  { key: 'international_info', label: 'International Student Info', placeholder: '{\n  "toefl_min": 100\n}', hint: 'JSON dict of international requirements + contacts.' },
  { key: 'school_outcomes', label: 'Aggregate Outcomes', placeholder: '{\n  "6mo_placement_rate": 0.95\n}', hint: 'JSON dict for school-wide placement stats.' },
]

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const authUser = useAuthStore(s => s.user)
  const [activeTab, setActiveTab] = useState('profile')

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'team', label: 'Team' },
    { id: 'review', label: 'Review' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'billing', label: 'Billing' },
    { id: 'account', label: 'My account' },
  ]

  // Shared per-user settings (security / preferences / notifications / account).
  const settingsQ = useQuery({ queryKey: ['institution-settings'], queryFn: getInstitutionSettings })
  const refetchSettings = () => queryClient.invalidateQueries({ queryKey: ['institution-settings'] })

  const updatePrefsMut = useMutation({
    mutationFn: (p: UpdateInstitutionSettingsPayload) => updateInstitutionSettings(p),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['institution-settings'] }),
    onError: e => showToast(e instanceof Error ? e.message : 'Could not save', 'error'),
  })

  // ── Profile (existing editor, rebranded) ──
  const instQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution })
  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) as any })
  const [instJsonText, setInstJsonText] = useState<Record<InstJsonKey, string>>({
    social_links: '', inquiry_routing: '', support_services: '', policies: '', international_info: '', school_outcomes: '',
  })
  const [instJsonErrors, setInstJsonErrors] = useState<Partial<Record<InstJsonKey, string>>>({})

  useEffect(() => {
    if (instQ.data) {
      const inst = instQ.data as any
      profileForm.reset({
        name: inst.name, type: inst.type, country: inst.country,
        region: inst.region ?? '', city: inst.city ?? '',
        website_url: inst.website_url ?? '', contact_email: inst.contact_email ?? '',
        logo_url: inst.logo_url ?? '', description_text: inst.description_text ?? '',
        campus_description: inst.campus_description ?? '', campus_setting: inst.campus_setting ?? '',
        student_body_size: inst.student_body_size ?? undefined, founded_year: inst.founded_year ?? undefined,
        media_gallery_text: Array.isArray(inst.media_gallery) ? inst.media_gallery.join('\n') : '',
      })
      setInstJsonText({
        social_links: inst.social_links ? JSON.stringify(inst.social_links, null, 2) : '',
        inquiry_routing: inst.inquiry_routing ? JSON.stringify(inst.inquiry_routing, null, 2) : '',
        support_services: inst.support_services ? JSON.stringify(inst.support_services, null, 2) : '',
        policies: inst.policies ? JSON.stringify(inst.policies, null, 2) : '',
        international_info: inst.international_info ? JSON.stringify(inst.international_info, null, 2) : '',
        school_outcomes: inst.school_outcomes ? JSON.stringify(inst.school_outcomes, null, 2) : '',
      })
    }
  }, [instQ.data, profileForm])

  const updateInstMut = useMutation({
    mutationFn: updateInstitution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution'] })
      showToast('Profile updated', 'success')
    },
    onError: () => showToast('Failed to update profile', 'error'),
  })

  const onSaveProfile = profileForm.handleSubmit(data => {
    const parsed: Partial<Record<InstJsonKey, unknown>> = {}
    const errs: Partial<Record<InstJsonKey, string>> = {}
    for (const { key } of INST_JSON_FIELDS) {
      const text = instJsonText[key]
      if (!text || !text.trim()) continue
      try { parsed[key] = JSON.parse(text) } catch (e: any) { errs[key] = `Invalid JSON: ${e?.message || 'parse error'}` }
    }
    if (Object.keys(errs).length) { setInstJsonErrors(errs); showToast('Please fix JSON errors before saving', 'error'); return }
    setInstJsonErrors({})
    const mediaGallery = (data.media_gallery_text ?? '').split('\n').map(s => s.trim()).filter(Boolean)
    updateInstMut.mutate({
      name: data.name, type: data.type, country: data.country,
      region: data.region || undefined, city: data.city || undefined,
      website_url: data.website_url || undefined, contact_email: data.contact_email || undefined,
      logo_url: data.logo_url || undefined, description_text: data.description_text || undefined,
      campus_description: data.campus_description || undefined,
      campus_setting: (data.campus_setting as 'urban' | 'suburban' | 'rural' | '') || undefined,
      student_body_size: data.student_body_size || undefined, founded_year: data.founded_year || undefined,
      media_gallery: mediaGallery.length ? mediaGallery : undefined,
      social_links: parsed.social_links as any, inquiry_routing: parsed.inquiry_routing as any,
      support_services: parsed.support_services as any, policies: parsed.policies as any,
      international_info: parsed.international_info as any, school_outcomes: parsed.school_outcomes as any,
    })
  })

  // ── Review (rubrics) ──
  const [showRubricForm, setShowRubricForm] = useState(false)
  const [rubricName, setRubricName] = useState('')
  const [criteria, setCriteria] = useState<{ name: string; weight: number }[]>([{ name: '', weight: 0 }])
  const rubricsQ = useQuery({ queryKey: ['rubrics'], queryFn: () => getRubrics(), enabled: activeTab === 'review' })
  const rubrics: Rubric[] = Array.isArray(rubricsQ.data) ? rubricsQ.data : []
  const createRubricMut = useMutation({
    mutationFn: createRubric,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rubrics'] })
      showToast('Rubric created', 'success')
      setShowRubricForm(false); setRubricName(''); setCriteria([{ name: '', weight: 0 }])
    },
    onError: () => showToast('Failed to create rubric', 'error'),
  })
  const handleCreateRubric = () => {
    if (!rubricName.trim()) { showToast('Name is required', 'warning'); return }
    const total = criteria.reduce((s, c) => s + c.weight, 0)
    if (total !== 100) { showToast(`Weights must sum to 100 (currently ${total})`, 'warning'); return }
    const valid = criteria.filter(c => c.name.trim())
    if (valid.length === 0) { showToast('Add at least one criterion', 'warning'); return }
    createRubricMut.mutate({ rubric_name: rubricName, criteria: valid })
  }
  const weightSum = criteria.reduce((s, c) => s + c.weight, 0)

  // ── Billing ──
  const billingQ = useQuery({ queryKey: ['institution-billing'], queryFn: getInstitutionBilling, enabled: activeTab === 'billing' })

  return (
    <div className="px-4 sm:px-6 py-6 space-y-5 max-w-3xl mx-auto w-full">
      <header className="flex items-center gap-2">
        <Settings size={22} className="text-secondary" />
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      </header>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Profile */}
      {activeTab === 'profile' && (
        <Card className="p-5 sm:p-6">
          {instQ.isLoading ? (
            <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (
            <form onSubmit={onSaveProfile} className="space-y-6">
              <div className="space-y-4">
                <Input label="Institution Name" required {...profileForm.register('name')} error={profileForm.formState.errors.name?.message} />
                <Select label="Type" required options={INSTITUTION_TYPES} {...profileForm.register('type')} error={profileForm.formState.errors.type?.message} />
                <Input label="Country" required {...profileForm.register('country')} error={profileForm.formState.errors.country?.message} />
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Region" {...profileForm.register('region')} />
                  <Input label="City" {...profileForm.register('city')} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Website URL" {...profileForm.register('website_url')} error={profileForm.formState.errors.website_url?.message} />
                  <Input label="Contact Email" {...profileForm.register('contact_email')} error={profileForm.formState.errors.contact_email?.message} />
                </div>
                <Input label="Logo URL (S3)" {...profileForm.register('logo_url')} error={profileForm.formState.errors.logo_url?.message} />
              </div>

              <div className="border-t border-border pt-4 space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Description &amp; Campus</h3>
                <Textarea label="Short description" {...profileForm.register('description_text')} rows={3} />
                <Textarea label="Campus description" {...profileForm.register('campus_description')} rows={3} />
                <div className="grid grid-cols-3 gap-4">
                  <Select label="Campus setting" options={CAMPUS_SETTING_OPTIONS} {...profileForm.register('campus_setting')} />
                  <Input label="Student body size" type="number" {...profileForm.register('student_body_size')} />
                  <Input label="Founded year" type="number" placeholder="e.g. 1831" {...profileForm.register('founded_year')} error={profileForm.formState.errors.founded_year?.message} />
                </div>
              </div>

              <div className="border-t border-border pt-4 space-y-2">
                <h3 className="text-sm font-semibold text-foreground">Media Gallery</h3>
                <p className="text-xs text-muted-foreground">One S3 URL per line. First entry is the hero image.</p>
                <textarea
                  className="w-full rounded-md border border-border bg-card text-foreground p-3 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                  rows={4}
                  {...profileForm.register('media_gallery_text')}
                />
              </div>

              {INST_JSON_FIELDS.map(({ key, label, placeholder, hint }) => (
                <div key={key} className="border-t border-border pt-4 space-y-2">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{label}</h3>
                    <p className="text-xs text-muted-foreground">{hint}</p>
                  </div>
                  <textarea
                    className="w-full rounded-md border border-border bg-card text-foreground p-3 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                    rows={5}
                    value={instJsonText[key]}
                    placeholder={placeholder}
                    onChange={e => setInstJsonText(prev => ({ ...prev, [key]: e.target.value }))}
                  />
                  {instJsonErrors[key] && <p className="text-xs text-error">{instJsonErrors[key]}</p>}
                </div>
              ))}

              <div className="flex justify-end">
                <Button type="submit" variant="secondary" loading={updateInstMut.isPending}>Save Changes</Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Team */}
      {activeTab === 'team' && <TeamCard />}

      {/* Review (rubrics) */}
      {activeTab === 'review' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button variant="secondary" onClick={() => setShowRubricForm(!showRubricForm)}>
              <Plus size={16} /> New Rubric
            </Button>
          </div>
          {showRubricForm && (
            <Card className="p-5 space-y-4">
              <h3 className="font-semibold text-foreground">Create Rubric</h3>
              <Input label="Rubric Name" required value={rubricName} onChange={e => setRubricName(e.target.value)} />
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-foreground">Criteria</label>
                  <span className={`text-xs font-medium ${weightSum === 100 ? 'text-success' : 'text-error'}`}>Total: {weightSum}/100</span>
                </div>
                {criteria.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 mb-2">
                    <Input className="flex-1" placeholder="Criterion name" value={c.name} onChange={e => setCriteria(criteria.map((x, idx) => idx === i ? { ...x, name: e.target.value } : x))} />
                    <Input className="w-20" type="number" value={c.weight} onChange={e => setCriteria(criteria.map((x, idx) => idx === i ? { ...x, weight: Number(e.target.value) } : x))} />
                    <button onClick={() => setCriteria(criteria.filter((_, idx) => idx !== i))} className="ui-btn p-1.5 text-muted-foreground hover:text-error"><Trash2 size={16} /></button>
                  </div>
                ))}
                <Button variant="ghost" size="sm" onClick={() => setCriteria([...criteria, { name: '', weight: 0 }])}><Plus size={14} /> Add Criterion</Button>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="tertiary" onClick={() => setShowRubricForm(false)}>Cancel</Button>
                <Button variant="secondary" onClick={handleCreateRubric} loading={createRubricMut.isPending}>Create</Button>
              </div>
            </Card>
          )}
          {rubricsQ.isLoading ? (
            <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
          ) : rubrics.length === 0 ? (
            <Card className="p-6 text-center text-sm text-muted-foreground">No rubrics yet. Create one to start scoring applications.</Card>
          ) : (
            rubrics.map(r => (
              <Card key={r.id} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-foreground">{r.rubric_name}</h3>
                  <Badge variant={r.is_active ? 'success' : 'neutral'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-2">Created {formatDate(r.created_at)}</p>
                {r.criteria && (
                  <div className="grid grid-cols-2 gap-1 text-xs text-muted-foreground">
                    {r.criteria.map(c => <span key={c.name}>{c.name}: {c.weight}%</span>)}
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}

      {/* Integrations */}
      {activeTab === 'integrations' && (
        <IntegrationsCard primaryDomain={settingsQ.data?.account.primary_domain ?? null} />
      )}

      {/* Notifications */}
      {activeTab === 'notifications' && (
        settingsQ.isLoading || !settingsQ.data ? (
          <Card className="p-6"><Skeleton className="h-40" /></Card>
        ) : (
          <NotificationsCard
            notifications={settingsQ.data.notifications}
            emailEnabled={settingsQ.data.email_enabled}
            emailFrequency={settingsQ.data.email_frequency}
            onChanged={refetchSettings}
          />
        )
      )}

      {/* Billing */}
      {activeTab === 'billing' && (
        <div className="space-y-4">
          {billingQ.isLoading || !billingQ.data ? (
            <Card className="p-6"><Skeleton className="h-28" /></Card>
          ) : (
            <>
              <Card className="p-5 sm:p-6">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground font-semibold">Current cycle · {billingQ.data.cycle_label}</p>
                    <p className="text-3xl font-bold text-foreground mt-1">${billingQ.data.current_charge_usd.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {billingQ.data.applicants_processed} unique applicant{billingQ.data.applicants_processed === 1 ? '' : 's'} processed × ${billingQ.data.per_applicant_usd}
                    </p>
                  </div>
                  <div className="h-14 w-14 rounded-xl bg-secondary/10 flex items-center justify-center">
                    <Users size={26} className="text-secondary" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-4 border-t border-border pt-3">
                  Usage-based pricing: <span className="font-medium text-foreground">${billingQ.data.per_applicant_usd} per unique applicant processed</span>. No per-seat fees.
                </p>
              </Card>
              <Card className="p-5 sm:p-6">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-3"><CreditCard size={16} className="text-secondary" /> Payment method</h3>
                {billingQ.data.has_payment_method ? (
                  <p className="text-sm text-foreground">{billingQ.data.payment_method_brand} •••• {billingQ.data.payment_method_last4}</p>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-muted-foreground">No payment method on file. Add one to enable automatic billing at cycle close.</p>
                    <a href="mailto:billing@unipaith.co?subject=Set%20up%20institution%20billing" className="inline-flex items-center px-3 h-9 text-sm font-medium rounded-lg border border-secondary text-secondary hover:bg-secondary/5 transition-colors whitespace-nowrap">Set up billing</a>
                  </div>
                )}
              </Card>
              {billingQ.data.invoices.length > 0 && (
                <Card className="p-5 sm:p-6">
                  <h3 className="text-sm font-semibold text-foreground mb-3">Invoices</h3>
                  <div className="divide-y divide-border">
                    {billingQ.data.invoices.map(inv => (
                      <div key={inv.id} className="flex items-center justify-between py-2 text-sm">
                        <span className="text-muted-foreground">{inv.description}</span>
                        <span className="text-foreground font-medium">${inv.amount_usd}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* My account — preferences + security (personal) */}
      {activeTab === 'account' && (
        settingsQ.isLoading || !settingsQ.data ? (
          <div className="space-y-4">{Array.from({ length: 2 }).map((_, i) => <Card key={i} className="p-6"><Skeleton className="h-40" /></Card>)}</div>
        ) : (
          <div className="space-y-5">
            <PreferencesCard preferences={settingsQ.data.preferences} onSave={p => updatePrefsMut.mutate(p)} saving={updatePrefsMut.isPending} />
            <SecurityCard
              mfaEnabled={settingsQ.data.security.mfa_enabled}
              mfaMethod={settingsQ.data.security.mfa_method}
              email={authUser?.email ?? ''}
              pendingEmail={null}
              onChanged={refetchSettings}
            />
          </div>
        )
      )}
    </div>
  )
}
