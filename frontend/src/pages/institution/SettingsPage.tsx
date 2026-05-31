import { useState, useEffect, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Plus, Trash2, CreditCard, Users } from 'lucide-react'
import { getInstitution, updateInstitution } from '../../api/institutions'
import { getRubrics, createRubric } from '../../api/reviews'
import { getInstitutionBilling } from '../../api/billing'
import { getNotificationPrefs, updateNotificationPrefs } from '../../api/notifications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { INSTITUTION_TYPES } from '../../utils/constants'
import { formatDate } from '../../utils/format'
import type { Rubric, NotificationPreference } from '../../types'
import {
  PairRowsEditor, LinkRowsEditor, MetricRowsEditor, StringListEditor,
} from './settings/ProfileJsonEditors'

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
})
type ProfileForm = z.infer<typeof profileSchema>

// Datalist suggestions for the guided JSONB editors (Spec 22 §3 / gap G-I1).
// The metric keys below mirror what student/institution/InstitutionDetail.tsx
// reads on the Overview/About tabs, so a guided entry feeds the rendered cards.
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
    <section className={divider ? 'border-t pt-4 space-y-4' : 'space-y-4'}>
      <div>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {hint && <p className="text-xs text-gray-500">{hint}</p>}
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
        <h4 className="text-[13px] font-semibold text-gray-700">{title}</h4>
        {hint && <p className="text-xs text-gray-500">{hint}</p>}
      </div>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('profile')

  // Rubric state
  const [showRubricForm, setShowRubricForm] = useState(false)
  const [rubricName, setRubricName] = useState('')
  const [criteria, setCriteria] = useState<{ name: string; weight: number }[]>([
    { name: '', weight: 0 },
  ])

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'rubrics', label: 'Rubrics' },
    { id: 'billing', label: 'Billing' },
    { id: 'notifications', label: 'Notifications' },
  ]

  // --- Billing (Spec 07 §4.2 / 21 §3.6) ---
  const billingQ = useQuery({
    queryKey: ['institution-billing'],
    queryFn: getInstitutionBilling,
    enabled: activeTab === 'billing',
  })

  // --- Profile ---
  const instQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution })
  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) as any })

  // The six institution-profile JSONB dicts (Spec 22 §3) + media gallery are
  // edited through guided row editors, not raw JSON. Held here as parsed values
  // and seeded from the loaded institution; editors re-seed on `inst.updated_at`.
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
        name: inst.name,
        type: inst.type,
        country: inst.country,
        region: inst.region ?? '',
        city: inst.city ?? '',
        website_url: inst.website_url ?? '',
        contact_email: inst.contact_email ?? '',
        logo_url: inst.logo_url ?? '',
        description_text: inst.description_text ?? '',
        campus_description: inst.campus_description ?? '',
        campus_setting: inst.campus_setting ?? '',
        student_body_size: inst.student_body_size ?? undefined,
        founded_year: inst.founded_year ?? undefined,
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
      name: data.name,
      type: data.type,
      country: data.country,
      region: data.region || undefined,
      city: data.city || undefined,
      website_url: data.website_url || undefined,
      contact_email: data.contact_email || undefined,
      logo_url: data.logo_url || undefined,
      description_text: data.description_text || undefined,
      campus_description: data.campus_description || undefined,
      campus_setting: (data.campus_setting as 'urban' | 'suburban' | 'rural' | '') || undefined,
      student_body_size: data.student_body_size || undefined,
      founded_year: data.founded_year || undefined,
      media_gallery: mediaGallery,
      social_links: socialLinks,
      inquiry_routing: inquiryRouting,
      support_services: supportServices,
      policies,
      international_info: internationalInfo,
      school_outcomes: schoolOutcomes,
    })
  })

  // --- Rubrics ---
  const rubricsQ = useQuery({ queryKey: ['rubrics'], queryFn: () => getRubrics() })
  const rubrics: Rubric[] = Array.isArray(rubricsQ.data) ? rubricsQ.data : []

  const createRubricMut = useMutation({
    mutationFn: createRubric,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rubrics'] })
      showToast('Rubric created', 'success')
      setShowRubricForm(false)
      setRubricName('')
      setCriteria([{ name: '', weight: 0 }])
    },
    onError: () => showToast('Failed to create rubric', 'error'),
  })

  const handleCreateRubric = () => {
    if (!rubricName.trim()) { showToast('Name is required', 'warning'); return }
    const total = criteria.reduce((s, c) => s + c.weight, 0)
    if (total !== 100) { showToast(`Weights must sum to 100 (currently ${total})`, 'warning'); return }
    const validCriteria = criteria.filter(c => c.name.trim())
    if (validCriteria.length === 0) { showToast('Add at least one criterion', 'warning'); return }
    createRubricMut.mutate({ rubric_name: rubricName, criteria: validCriteria })
  }

  const addCriterion = () => setCriteria([...criteria, { name: '', weight: 0 }])
  const removeCriterion = (i: number) => setCriteria(criteria.filter((_, idx) => idx !== i))
  const updateCriterion = (i: number, field: 'name' | 'weight', value: string | number) => {
    setCriteria(criteria.map((c, idx) => idx === i ? { ...c, [field]: value } : c))
  }

  // --- Notifications ---
  const notifsQ = useQuery({ queryKey: ['notification-prefs'], queryFn: getNotificationPrefs })
  const notifPrefs: NotificationPreference | undefined = notifsQ.data
  const [emailEnabled, setEmailEnabled] = useState(true)
  const [prefs, setPrefs] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (notifPrefs) {
      setEmailEnabled(notifPrefs.email_enabled)
      setPrefs(notifPrefs.preferences)
    }
  }, [notifPrefs])

  const updateNotifMut = useMutation({
    mutationFn: updateNotificationPrefs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-prefs'] })
      showToast('Notification preferences updated', 'success')
    },
    onError: () => showToast('Failed to update preferences', 'error'),
  })

  const handleSaveNotifs = () => {
    updateNotifMut.mutate({ email_enabled: emailEnabled, preferences: prefs })
  }

  const togglePref = (key: string) => setPrefs({ ...prefs, [key]: !prefs[key] })

  const weightSum = criteria.reduce((s, c) => s + c.weight, 0)

  const inst = instQ.data as any
  // Re-seed the guided editors whenever fresh server data arrives (incl. after a
  // save), but stay stable across keystrokes so editing is smooth.
  const seedKey = inst?.updated_at ?? 'init'

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <div className="flex items-center gap-2">
        <Settings size={24} className="text-brand-slate-600" />
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card className="p-6">
          {instQ.isLoading || !inst ? (
            <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (
            <form onSubmit={onSaveProfile} className="space-y-6">
              {/* Identity (Spec 22 §3) */}
              <Section title="Identity" hint="Core facts shown on your public profile card and header." divider={false}>
                <Input label="Institution Name *" {...profileForm.register('name')} error={profileForm.formState.errors.name?.message} />
                <Select label="Type *" options={INSTITUTION_TYPES} {...profileForm.register('type')} error={profileForm.formState.errors.type?.message} />
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Country *" {...profileForm.register('country')} error={profileForm.formState.errors.country?.message} />
                  <Input label="Founded year" type="number" placeholder="e.g. 1831" {...profileForm.register('founded_year')} error={profileForm.formState.errors.founded_year?.message} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Region" {...profileForm.register('region')} />
                  <Input label="City" {...profileForm.register('city')} />
                </div>
              </Section>

              {/* Campus */}
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

              {/* Web presence */}
              <Section title="Web presence" hint="Where students reach you online.">
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Website URL" {...profileForm.register('website_url')} error={profileForm.formState.errors.website_url?.message} />
                  <Input label="Contact Email" {...profileForm.register('contact_email')} error={profileForm.formState.errors.contact_email?.message} />
                </div>
                <Input label="Logo URL (S3)" {...profileForm.register('logo_url')} error={profileForm.formState.errors.logo_url?.message} />
                <Field title="Social links" hint="Platform → profile URL. Shown in your public header.">
                  <PairRowsEditor key={`sl-${seedKey}`} initial={inst.social_links} onChange={setSocialLinks}
                    keyLabel="Platform" valueLabel="Profile URL" keySuggestions={SOCIAL_SUGGESTIONS}
                    valuePlaceholder="https://…" valueType="url" addLabel="Add social link" />
                </Field>
              </Section>

              {/* Story & support */}
              <Section title="Story & support" hint="Your description and the support services students care about.">
                <Textarea label="Short description" {...profileForm.register('description_text')} rows={3} />
                <Field title="Support services" hint="Shown on the public About tab (tutoring, career, counseling, …).">
                  <LinkRowsEditor key={`ss-${seedKey}`} initial={inst.support_services} onChange={setSupportServices}
                    withSummary={false} nameLabel="Service name" nameSuggestions={SUPPORT_SUGGESTIONS} addLabel="Add support service" />
                </Field>
              </Section>

              {/* Policies & international */}
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

              {/* Outcomes */}
              <Section title="Outcomes" hint="Institution-wide stats, distinct from program outcomes. A number 0–1 renders as a percentage on the Overview tab.">
                <MetricRowsEditor key={`out-${seedKey}`} initial={inst.school_outcomes} onChange={setSchoolOutcomes}
                  keySuggestions={OUTCOME_SUGGESTIONS} addLabel="Add outcome metric" />
              </Section>

              {/* Inquiry routing */}
              <Section title="Inquiry routing" hint="Where ‘Request info’ inquiries from your page should go, by type (email or URL).">
                <PairRowsEditor key={`ir-${seedKey}`} initial={inst.inquiry_routing} onChange={setInquiryRouting}
                  keyLabel="Inquiry type" valueLabel="Destination" keySuggestions={INQUIRY_TYPE_SUGGESTIONS}
                  valuePlaceholder="admissions@example.edu" addLabel="Add routing rule" />
              </Section>

              <div className="flex justify-end">
                <Button type="submit" disabled={updateInstMut.isPending}>
                  {updateInstMut.isPending ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Rubrics Tab */}
      {activeTab === 'rubrics' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowRubricForm(!showRubricForm)} className="flex items-center gap-2">
              <Plus size={16} /> New Rubric
            </Button>
          </div>

          {showRubricForm && (
            <Card className="p-5 space-y-4">
              <h3 className="font-semibold text-gray-900">Create Rubric</h3>
              <Input label="Rubric Name *" value={rubricName} onChange={e => setRubricName(e.target.value)} />
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Criteria</label>
                  <span className={`text-xs font-medium ${weightSum === 100 ? 'text-green-600' : 'text-red-600'}`}>
                    Total: {weightSum}/100
                  </span>
                </div>
                {criteria.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 mb-2">
                    <Input className="flex-1" placeholder="Criterion name" value={c.name} onChange={e => updateCriterion(i, 'name', e.target.value)} />
                    <Input className="w-20" type="number" value={c.weight} onChange={e => updateCriterion(i, 'weight', Number(e.target.value))} />
                    <button onClick={() => removeCriterion(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
                  </div>
                ))}
                <Button variant="ghost" size="sm" onClick={addCriterion} className="flex items-center gap-1">
                  <Plus size={14} /> Add Criterion
                </Button>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setShowRubricForm(false)}>Cancel</Button>
                <Button onClick={handleCreateRubric} disabled={createRubricMut.isPending}>
                  {createRubricMut.isPending ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </Card>
          )}

          {rubricsQ.isLoading ? (
            <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
          ) : rubrics.length === 0 ? (
            <Card className="p-6 text-center text-sm text-gray-500">No rubrics yet. Create one to start scoring applications.</Card>
          ) : (
            rubrics.map(r => (
              <Card key={r.id} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{r.rubric_name}</h3>
                  <Badge variant={r.is_active ? 'success' : 'neutral'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>
                </div>
                <p className="text-xs text-gray-400 mb-2">Created {formatDate(r.created_at)}</p>
                {r.criteria && (
                  <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                    {r.criteria.map(c => (
                      <span key={c.name}>{c.name}: {c.weight}%</span>
                    ))}
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}

      {/* Billing Tab — usage-based ($15/unique applicant), Spec 07 §4.2 */}
      {activeTab === 'billing' && (
        <div className="space-y-4">
          {billingQ.isLoading || !billingQ.data ? (
            <Card className="p-6"><Skeleton className="h-28" /></Card>
          ) : (
            <>
              <Card className="p-6">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold">Current cycle · {billingQ.data.cycle_label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      ${billingQ.data.current_charge_usd.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {billingQ.data.applicants_processed} unique applicant{billingQ.data.applicants_processed === 1 ? '' : 's'} processed
                      {' '}× ${billingQ.data.per_applicant_usd}
                    </p>
                  </div>
                  <div className="h-14 w-14 rounded-xl bg-cobalt/10 flex items-center justify-center">
                    <Users size={26} className="text-cobalt" />
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4 border-t pt-3">
                  Usage-based pricing: <span className="font-medium text-gray-700">${billingQ.data.per_applicant_usd} per unique applicant processed</span>.
                  No per-seat fees. You’re only billed for applicants who submit to your programs.
                </p>
              </Card>

              <Card className="p-6">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
                  <CreditCard size={16} className="text-cobalt" /> Payment method
                </h3>
                {billingQ.data.has_payment_method ? (
                  <p className="text-sm text-gray-700">{billingQ.data.payment_method_brand} •••• {billingQ.data.payment_method_last4}</p>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-gray-500">No payment method on file. Add one to enable automatic billing at cycle close.</p>
                    <a
                      href="mailto:billing@unipaith.co?subject=Set%20up%20institution%20billing"
                      className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-cobalt text-cobalt hover:bg-cobalt/5 transition-colors whitespace-nowrap"
                    >
                      Set up billing
                    </a>
                  </div>
                )}
              </Card>

              {billingQ.data.invoices.length > 0 && (
                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Invoices</h3>
                  <div className="divide-y">
                    {billingQ.data.invoices.map(inv => (
                      <div key={inv.id} className="flex items-center justify-between py-2 text-sm">
                        <span className="text-gray-700">{inv.description}</span>
                        <span className="text-gray-900 font-medium">${inv.amount_usd}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card className="p-6 space-y-4">
          {notifsQ.isLoading ? (
            <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Email Notifications</p>
                  <p className="text-xs text-gray-500">Receive notifications via email</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" checked={emailEnabled} onChange={() => setEmailEnabled(!emailEnabled)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-brand-slate-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-slate-600"></div>
                </label>
              </div>

              <hr />

              {Object.entries(prefs).length > 0 ? (
                Object.entries(prefs).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between">
                    <p className="text-sm text-gray-700 capitalize">{key.replace(/_/g, ' ')}</p>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" checked={enabled} onChange={() => togglePref(key)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-brand-slate-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-slate-600"></div>
                    </label>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">No notification preferences configured yet.</p>
              )}

              <div className="flex justify-end">
                <Button onClick={handleSaveNotifs} disabled={updateNotifMut.isPending}>
                  {updateNotifMut.isPending ? 'Saving...' : 'Save Preferences'}
                </Button>
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  )
}
