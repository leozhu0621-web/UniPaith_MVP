import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Plus, Trash2 } from 'lucide-react'
import { getInstitution, updateInstitution } from '../../api/institutions'
import { getRubrics, createRubric } from '../../api/reviews'
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

const profileSchema = z.object({
  name: z.string().min(1, 'Required'),
  type: z.string().min(1, 'Required'),
  country: z.string().min(1, 'Required'),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal('')),
  description_text: z.string().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

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
    { id: 'notifications', label: 'Notifications' },
  ]

  // --- Profile ---
  const instQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution })
  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) })

  useEffect(() => {
    if (instQ.data) {
      const inst = instQ.data
      profileForm.reset({
        name: inst.name,
        type: inst.type,
        country: inst.country,
        region: inst.region ?? '',
        city: inst.city ?? '',
        website_url: inst.website_url ?? '',
        description_text: inst.description_text ?? '',
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
    updateInstMut.mutate({
      name: data.name,
      type: data.type,
      country: data.country,
      region: data.region || undefined,
      city: data.city || undefined,
      website_url: data.website_url || undefined,
      description_text: data.description_text || undefined,
    })
  })

  // --- Rubrics ---
  const rubricsQ = useQuery({ queryKey: ['rubrics'], queryFn: () => getRubrics() })
  const rubrics: Rubric[] = rubricsQ.data ?? []

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

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <div className="flex items-center gap-2">
        <Settings size={24} className="text-indigo-600" />
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card className="p-6">
          {instQ.isLoading ? (
            <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (
            <form onSubmit={onSaveProfile} className="space-y-4">
              <Input label="Institution Name *" {...profileForm.register('name')} error={profileForm.formState.errors.name?.message} />
              <Select label="Type *" options={INSTITUTION_TYPES} {...profileForm.register('type')} error={profileForm.formState.errors.type?.message} />
              <Input label="Country *" {...profileForm.register('country')} error={profileForm.formState.errors.country?.message} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Region" {...profileForm.register('region')} />
                <Input label="City" {...profileForm.register('city')} />
              </div>
              <Input label="Website URL" {...profileForm.register('website_url')} />
              <Textarea label="Description" {...profileForm.register('description_text')} rows={3} />
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
                  <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              <hr />

              {Object.entries(prefs).length > 0 ? (
                Object.entries(prefs).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between">
                    <p className="text-sm text-gray-700 capitalize">{key.replace(/_/g, ' ')}</p>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" checked={enabled} onChange={() => togglePref(key)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
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
