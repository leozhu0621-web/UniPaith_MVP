import { useState, useEffect, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Plus, Trash2, CreditCard, Users } from 'lucide-react'
import { getInstitution, updateInstitution } from '../../api/institutions'
import { getRubrics, createRubric } from '../../api/reviews'
import { getInstitutionBilling } from '../../api/billing'
import {
  getInstitutionSettings,
  updateInstitutionSettings,
  type UpdateInstitutionSettingsPayload,
} from '../../api/settings'
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
import {
  PairRowsEditor, LinkRowsEditor, MetricRowsEditor, StringListEditor,
} from './settings/ProfileJsonEditors'
import SecurityCard from '../student/settings/SecurityCard'
import PreferencesCard from '../student/settings/PreferencesCard'
import NotificationsCard from '../student/settings/NotificationsCard'
import TeamCard from './settings/TeamCard'
import IntegrationsCard from './settings/IntegrationsCard'
import OrgAccountCard from './settings/OrgAccountCard'
import ReviewConfigCard from './settings/ReviewConfigCard'
import AIConfigCard from './settings/AIConfigCard'
import FeeConfigCard from './settings/FeeConfigCard'

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
  contact_phone: z.string().optional(),
  logo_url: z.string().url().optional().or(z.literal('')),
  description_text: z.string().optional(),
  campus_description: z.string().optional(),
  campus_setting: z.string().optional(),
  student_body_size: z.coerce.number().int().nonnegative().optional(),
  founded_year: z.coerce.number().int().nonnegative().optional(),
  accreditation: z.string().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

// Datalist suggestions for the guided JSONB editors (Spec 22 §3 / gap G-I1).
const SOCIAL_SUGGESTIONS = ['twitter', 'linkedin', 'instagram', 'youtube', 'facebook', 'tiktok']
const INQUIRY_TYPE_SUGGESTIONS = ['general', 'international', 'financial_aid', 'undergraduate', 'graduate', 'transfer']
const SUPPORT_SUGGESTIONS = ['Tutoring', 'Career services', 'Counseling', 'Disability services', 'First-gen support', 'Financial literacy']
const POLICY_SUGGESTIONS = ['Transfer credit', 'Code of conduct', 'Admissions policy', 'Test policy', 'Refund policy']
const INTL_SUGGESTIONS = ['toefl_min', 'ielts_min', 'duolingo_min', 'visa_contact', 'visa_url', 'supported_visas', 'application_fee']
const OUTCOME_SUGGESTIONS = ['employed_or_continuing_ed', 'graduation_rate_6yr', 'first_destination_placement_rate', 'median_starting_salary', 'top_employers', 'top_employer_industries', 'source']

type Dict = Record<string, unknown>

/** Section wrapper for the Profile form — matches the existing settings idiom. */
function Section({ title, hint, children, divider = true }: { title: string; hint?: string; children: ReactNode; divider?: boolean }) {
  return (
    <section className={divider ? 'border-t border-border pt-4 space-y-4' : 'space-y-4'}>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </section>
  )
}

/** Labelled wrapper for a guided editor inside a section. */
function Field({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <div>
        <h4 className="text-[13px] font-semibold text-foreground">{title}</h4>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const authUser = useAuthStore(s => s.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState('account')

  const tabs = [
    { id: 'account', label: 'Account' },
    { id: 'profile', label: 'Public profile' },
    { id: 'team', label: 'Team' },
    { id: 'review', label: 'Rubrics' },
    { id: 'ai', label: 'AI' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'billing', label: 'Billing' },
    { id: 'security', label: 'Security' },
  ]

  // Spec 32 §3 — `/i/settings?tab=rubrics` maps to the review/rubrics panel.
  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab === 'rubrics') setActiveTab('review')
    else if (tab && tabs.some(t => t.id === tab)) setActiveTab(tab)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', tab === 'review' ? 'rubrics' : tab)
      return next
    })
  }

  // Shared per-user settings (security / preferences / notifications / account).
  const settingsQ = useQuery({ queryKey: ['institution-settings'], queryFn: getInstitutionSettings })
  const refetchSettings = () => queryClient.invalidateQueries({ queryKey: ['institution-settings'] })
  const updatePrefsMut = useMutation({
    mutationFn: (p: UpdateInstitutionSettingsPayload) => updateInstitutionSettings(p),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['institution-settings'] }),
    onError: e => showToast(e instanceof Error ? e.message : 'Could not save', 'error'),
  })

  // Rubric state
  const [showRubricForm, setShowRubricForm] = useState(false)
  const [rubricName, setRubricName] = useState('')
  const [criteria, setCriteria] = useState<{ name: string; weight: number }[]>([{ name: '', weight: 0 }])

  // --- Billing ---
  const billingQ = useQuery({
    queryKey: ['institution-billing'],
    queryFn: getInstitutionBilling,
    enabled: activeTab === 'billing',
  })

  // --- Profile (Spec 22 guided editor) ---
  const instQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution })
  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) as any })

  const [socialLinks, setSocialLinks] = useState<Dict>({})
  const [inquiryRouting, setInquiryRouting] = useState<Dict>({})
  const [supportServices, setSupportServices] = useState<Dict>({})
  const [policies, setPolicies] = useState<Dict>({})
  const [internationalInfo, setInternationalInfo] = useState<Dict>({})
  const [schoolOutcomes, setSchoolOutcomes] = useState<Dict>({})
  const [mediaGallery, setMediaGallery] = useState<string[]>([])

  useEffect(() => {
    if (instQ.data) {
      const inst = instQ.data as any
      profileForm.reset({
        name: inst.name, type: inst.type, country: inst.country,
        region: inst.region ?? '', city: inst.city ?? '',
        website_url: inst.website_url ?? '', contact_email: inst.contact_email ?? '',
        contact_phone: inst.contact_phone ?? '',
        logo_url: inst.logo_url ?? '', description_text: inst.description_text ?? '',
        campus_description: inst.campus_description ?? '', campus_setting: inst.campus_setting ?? '',
        student_body_size: inst.student_body_size ?? undefined, founded_year: inst.founded_year ?? undefined,
        accreditation: (inst.ranking_data as any)?.accreditor ?? '',
      })
      setSocialLinks(inst.social_links ?? {})
      setInquiryRouting(inst.inquiry_routing ?? {})
      setSupportServices(inst.support_services ?? {})
      setPolicies(inst.policies ?? {})
      setInternationalInfo(inst.international_info ?? {})
      setSchoolOutcomes(inst.school_outcomes ?? {})
      setMediaGallery(Array.isArray(inst.media_gallery) ? inst.media_gallery : [])
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

  const onSaveProfile = profileForm.handleSubmit((data) => {
    updateInstMut.mutate({
      name: data.name, type: data.type, country: data.country,
      region: data.region || undefined, city: data.city || undefined,
      website_url: data.website_url || undefined, contact_email: data.contact_email || undefined,
      contact_phone: data.contact_phone?.trim() || undefined,
      logo_url: data.logo_url || undefined, description_text: data.description_text || undefined,
      campus_description: data.campus_description || undefined,
      campus_setting: (data.campus_setting as 'urban' | 'suburban' | 'rural' | '') || undefined,
      student_body_size: data.student_body_size || undefined, founded_year: data.founded_year || undefined,
      accreditation: data.accreditation?.trim() || undefined,
      media_gallery: mediaGallery,
      social_links: socialLinks, inquiry_routing: inquiryRouting, support_services: supportServices,
      policies, international_info: internationalInfo, school_outcomes: schoolOutcomes,
    })
  })

  // --- Review (rubrics) ---
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
  const updateCriterion = (i: number, field: 'name' | 'weight', value: string | number) =>
    setCriteria(criteria.map((c, idx) => (idx === i ? { ...c, [field]: value } : c)))
  const weightSum = criteria.reduce((s, c) => s + c.weight, 0)

  const inst = instQ.data as any
  const seedKey = inst?.updated_at ?? 'init'

  return (
    <div className="px-4 sm:px-6 py-6 space-y-5 max-w-3xl mx-auto w-full">
      <header className="flex items-center gap-2">
        <Settings size={22} className="text-secondary" />
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      </header>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />

      {activeTab === 'account' && (
        settingsQ.isLoading || !settingsQ.data ? (
          <Card className="p-6"><Skeleton className="h-40" /></Card>
        ) : (
          <OrgAccountCard account={settingsQ.data.account} onChanged={refetchSettings} />
        )
      )}

      {/* Public profile (Spec 22 guided editor) */}
      {activeTab === 'profile' && (
        <Card className="p-5 sm:p-6">
          {instQ.isLoading || !inst ? (
            <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (
            <form onSubmit={onSaveProfile} className="space-y-6">
              <Section title="Identity" hint="Core facts shown on your public profile card and header." divider={false}>
                <Input label="Institution Name" required {...profileForm.register('name')} error={profileForm.formState.errors.name?.message} />
                <Select label="Type" required options={INSTITUTION_TYPES} {...profileForm.register('type')} error={profileForm.formState.errors.type?.message} />
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Country" required {...profileForm.register('country')} error={profileForm.formState.errors.country?.message} />
                  <Input label="Founded year" type="number" placeholder="e.g. 1831" {...profileForm.register('founded_year')} error={profileForm.formState.errors.founded_year?.message} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Region" {...profileForm.register('region')} />
                  <Input label="City" {...profileForm.register('city')} />
                </div>
                <Input label="Accreditation" {...profileForm.register('accreditation')} placeholder="e.g. Middle States Commission on Higher Education" />
              </Section>

              <Section title="Campus" hint="The environment and scale of your campus.">
                <div className="grid grid-cols-2 gap-4">
                  <Select label="Campus setting" options={CAMPUS_SETTING_OPTIONS} {...profileForm.register('campus_setting')} />
                  <Input label="Student body size" type="number" {...profileForm.register('student_body_size')} />
                </div>
                <Textarea label="Campus description" {...profileForm.register('campus_description')} rows={3} placeholder="How the campus looks and feels, where it's located..." />
                <Field title="Media gallery" hint="Text-only per brand — S3 image URLs, one per row. The first is the hero.">
                  <StringListEditor key={`mg-${seedKey}`} initial={Array.isArray(inst.media_gallery) ? inst.media_gallery : []} onChange={setMediaGallery} placeholder="https://…/campus.jpg" addLabel="Add image URL" />
                </Field>
              </Section>

              <Section title="Web presence" hint="Where students reach you online.">
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Website URL" {...profileForm.register('website_url')} error={profileForm.formState.errors.website_url?.message} />
                  <Input label="Contact Email" {...profileForm.register('contact_email')} error={profileForm.formState.errors.contact_email?.message} />
                </div>
                <Input label="Contact Phone" {...profileForm.register('contact_phone')} placeholder="e.g. +1 (212) 555-0100" />
                <Input label="Logo URL (S3)" {...profileForm.register('logo_url')} error={profileForm.formState.errors.logo_url?.message} />
                <Field title="Social links" hint="Platform → profile URL. Shown in your public header.">
                  <PairRowsEditor key={`sl-${seedKey}`} initial={inst.social_links} onChange={setSocialLinks}
                    keyLabel="Platform" valueLabel="Profile URL" keySuggestions={SOCIAL_SUGGESTIONS}
                    valuePlaceholder="https://…" valueType="url" addLabel="Add social link" />
                </Field>
              </Section>

              <Section title="Story & support" hint="Your description and the support services students care about.">
                <Textarea label="Short description" {...profileForm.register('description_text')} rows={3} />
                <Field title="Support services" hint="Shown on the public About tab (tutoring, career, counseling, …).">
                  <LinkRowsEditor key={`ss-${seedKey}`} initial={inst.support_services} onChange={setSupportServices}
                    withSummary={false} nameLabel="Service name" nameSuggestions={SUPPORT_SUGGESTIONS} addLabel="Add support service" />
                </Field>
              </Section>

              <Section title="Policies & international" hint="Admissions, transfer and international guidance.">
                <Field title="Policies" hint="Each shows its name, an optional summary and a link on the About tab.">
                  <LinkRowsEditor key={`pol-${seedKey}`} initial={inst.policies} onChange={setPolicies}
                    withSummary nameLabel="Policy name" nameSuggestions={POLICY_SUGGESTIONS} addLabel="Add policy" />
                </Field>
                <Field title="International student info" hint="Test minimums, visa contacts, supported visas, etc.">
                  <MetricRowsEditor key={`intl-${seedKey}`} initial={inst.international_info} onChange={setInternationalInfo}
                    keySuggestions={INTL_SUGGESTIONS} addLabel="Add international detail" />
                </Field>
              </Section>

              <Section title="Outcomes" hint="Institution-wide stats, distinct from program outcomes. A number 0–1 renders as a percentage on the Overview tab.">
                <MetricRowsEditor key={`out-${seedKey}`} initial={inst.school_outcomes} onChange={setSchoolOutcomes}
                  keySuggestions={OUTCOME_SUGGESTIONS} addLabel="Add outcome metric" />
              </Section>

              <Section title="Inquiry routing" hint="Where ‘Request info’ inquiries from your page should go, by type (email or URL).">
                <PairRowsEditor key={`ir-${seedKey}`} initial={inst.inquiry_routing} onChange={setInquiryRouting}
                  keyLabel="Inquiry type" valueLabel="Destination" keySuggestions={INQUIRY_TYPE_SUGGESTIONS}
                  valuePlaceholder="admissions@example.edu" addLabel="Add routing rule" />
              </Section>

              <div className="flex justify-end">
                <Button type="submit" variant="secondary" loading={updateInstMut.isPending}>Save Changes</Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Team */}
      {activeTab === 'team' && <TeamCard />}

      {/* Review (config + rubrics) */}
      {activeTab === 'review' && (
        <div className="space-y-4">
          {settingsQ.isLoading || !settingsQ.data ? (
            <Card className="p-6"><Skeleton className="h-32" /></Card>
          ) : (
            <ReviewConfigCard config={settingsQ.data.review_config} onChanged={refetchSettings} />
          )}
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
                    <Input className="flex-1" placeholder="Criterion name" value={c.name} onChange={e => updateCriterion(i, 'name', e.target.value)} />
                    <Input className="w-20" type="number" value={c.weight} onChange={e => updateCriterion(i, 'weight', Number(e.target.value))} />
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

      {/* AI extensibility (Spec 37 §5) */}
      {activeTab === 'ai' && (
        settingsQ.isLoading || !settingsQ.data ? (
          <Card className="p-6"><Skeleton className="h-40" /></Card>
        ) : (
          <AIConfigCard config={settingsQ.data.ai_config} onChanged={refetchSettings} />
        )
      )}

      {/* Integrations */}
      {activeTab === 'integrations' && (
        <IntegrationsCard primaryDomain={settingsQ.data?.account.primary_domain ?? null} />
      )}

      {/* Notifications (matrix) */}
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
          {/* Spec 39 — applicant-facing fee & deposit collection config. */}
          <FeeConfigCard />
          <h2 className="text-sm font-semibold text-muted-foreground pt-2">Platform usage billing</h2>
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

      {/* Security + personal preferences (§3.7) */}
      {activeTab === 'security' && (
        settingsQ.isLoading || !settingsQ.data ? (
          <div className="space-y-4">{Array.from({ length: 2 }).map((_, i) => <Card key={i} className="p-6"><Skeleton className="h-40" /></Card>)}</div>
        ) : (
          <div className="space-y-5">
            <SecurityCard
              mfaEnabled={settingsQ.data.security.mfa_enabled}
              mfaMethod={settingsQ.data.security.mfa_method}
              email={authUser?.email ?? ''}
              pendingEmail={null}
              onChanged={refetchSettings}
            />
            <PreferencesCard preferences={settingsQ.data.preferences} onSave={p => updatePrefsMut.mutate(p)} saving={updatePrefsMut.isPending} />
          </div>
        )
      )}
    </div>
  )
}
