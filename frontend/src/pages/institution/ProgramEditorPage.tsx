import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Send, EyeOff, AlertTriangle, Layers } from 'lucide-react'
import {
  getInstitution,
  getInstitutionSchools,
  getInstitutionProgram,
  createProgram,
  updateProgram,
  publishProgram,
  unpublishProgram,
  type PublishValidationDetail,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { SectionCard, Repeatable, Toggle, ChipsInput, MiniLabel } from './program-editor/widgets'
import {
  type EditorDraft,
  type SectionId,
  SECTIONS,
  DEGREE_OPTIONS,
  DELIVERY_FORMAT_OPTIONS,
  CAMPUS_SETTING_OPTIONS,
  TUITION_PERIOD_OPTIONS,
  TEST_STANCE_OPTIONS,
  REC_TYPE_OPTIONS,
  PROMOTION_CATEGORY_OPTIONS,
  ENGLISH_TEST_OPTIONS,
  emptyDraft,
  fromProgram,
  toPayload,
  emptyRound,
} from './program-editor/helpers'

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

  // Sub-schools for the Identity picker (Spec 23 §2.1).
  const institutionQ = useQuery({ queryKey: ['institution-me'], queryFn: getInstitution })
  const schoolsQ = useQuery({
    queryKey: ['institution-schools', institutionQ.data?.id],
    queryFn: () => getInstitutionSchools(institutionQ.data!.id),
    enabled: !!institutionQ.data?.id,
  })

  const [draft, setDraft] = useState<EditorDraft>(emptyDraft)
  const [baselineVersion, setBaselineVersion] = useState<number | undefined>(undefined)
  const [published, setPublished] = useState(false)
  const [appsCount, setAppsCount] = useState(0)
  const [validation, setValidation] = useState<PublishValidationDetail | null>(null)
  const [conflict, setConflict] = useState(false)
  const [openSections, setOpenSections] = useState<Set<string>>(
    () => new Set(SECTIONS.map(s => s.id)),
  )
  const loadedRef = useRef(false)

  useEffect(() => {
    if (programQ.data && !loadedRef.current) {
      loadedRef.current = true
      setDraft(fromProgram(programQ.data))
      setBaselineVersion(programQ.data.version ?? programQ.data.feature_version)
      setPublished(!!programQ.data.is_published)
      setAppsCount(programQ.data.applications_count ?? 0)
    }
  }, [programQ.data])

  const schoolOptions = useMemo(
    () => [
      { value: '', label: '— No sub-school —' },
      ...((schoolsQ.data ?? []) as any[]).map(s => ({ value: s.id, label: s.name })),
    ],
    [schoolsQ.data],
  )

  // ── Draft updaters ─────────────────────────────────────────────────────────
  const set = <K extends keyof EditorDraft>(key: K, value: EditorDraft[K]) =>
    setDraft(d => ({ ...d, [key]: value }))
  const setCost = (patch: Partial<EditorDraft['cost_data']>) =>
    setDraft(d => ({ ...d, cost_data: { ...d.cost_data, ...patch } }))
  const setOutcomes = (patch: Partial<EditorDraft['outcomes_data']>) =>
    setDraft(d => ({ ...d, outcomes_data: { ...d.outcomes_data, ...patch } }))
  const setReqs = (patch: Partial<EditorDraft['application_requirements']>) =>
    setDraft(d => ({ ...d, application_requirements: { ...d.application_requirements, ...patch } }))
  const setTestPolicy = (patch: Partial<EditorDraft['application_requirements']['test_policy']>) =>
    setDraft(d => ({
      ...d,
      application_requirements: {
        ...d.application_requirements,
        test_policy: { ...d.application_requirements.test_policy, ...patch },
      },
    }))
  const setEnglish = (patch: Partial<EditorDraft['english_policy']>) =>
    setDraft(d => ({ ...d, english_policy: { ...d.english_policy, ...patch } }))

  // ── Mutations ────────────────────────────────────────────────────────────────
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
    queryClient.invalidateQueries({ queryKey: ['institution-program', id] })
  }

  const createMut = useMutation({
    mutationFn: () => createProgram(toPayload(draft) as any),
    onSuccess: data => {
      invalidate()
      showToast('Program created', 'success')
      navigate(`/i/programs/${data.id}/edit`)
    },
    onError: () => showToast('Failed to create program', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: () => updateProgram(id!, toPayload(draft) as any, baselineVersion),
    onSuccess: data => {
      invalidate()
      setBaselineVersion(data.version ?? data.feature_version)
      setAppsCount(data.applications_count ?? appsCount)
      showToast('Draft saved', 'success')
    },
    onError: (err: any) => {
      if (err?.response?.status === 409) setConflict(true)
      else showToast('Failed to save', 'error')
    },
  })

  const publishMut = useMutation({
    mutationFn: () => publishProgram(id!),
    onSuccess: data => {
      invalidate()
      setPublished(!!data.is_published)
      setBaselineVersion(data.version ?? data.feature_version)
      showToast('Program published', 'success')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      if (err?.response?.status === 422 && detail?.missing_fields) setValidation(detail)
      else showToast('Failed to publish', 'error')
    },
  })

  const unpublishMut = useMutation({
    mutationFn: () => unpublishProgram(id!),
    onSuccess: data => {
      invalidate()
      setPublished(!!data.is_published)
      showToast('Program unpublished', 'success')
    },
    onError: () => showToast('Failed to unpublish', 'error'),
  })

  const saving =
    createMut.isPending || updateMut.isPending || publishMut.isPending || unpublishMut.isPending

  const clientGate = (): boolean => {
    if (!draft.program_name.trim()) {
      showToast('Program name is required', 'warning')
      goToSection('identity')
      return false
    }
    if (!draft.degree_type) {
      showToast('Degree type is required', 'warning')
      goToSection('identity')
      return false
    }
    return true
  }

  const onSaveDraft = async () => {
    if (!clientGate()) return
    if (isEdit) updateMut.mutate()
    else createMut.mutate()
  }

  const onPublish = async () => {
    if (!clientGate()) return
    if (!isEdit) {
      // A program must be persisted before it can be published. Create the
      // draft first; the institution lands on the edit route and publishes there.
      showToast('Draft created — review required fields, then Publish.', 'info')
      createMut.mutate()
      return
    }
    try {
      await updateMut.mutateAsync()
      await publishMut.mutateAsync()
    } catch {
      /* 409 / 422 surfaced via the mutation onError handlers (modals) */
    }
  }

  // ── Section navigation ───────────────────────────────────────────────────────
  const goToSection = (sectionId: SectionId | string) => {
    setOpenSections(prev => new Set(prev).add(sectionId))
    setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 30)
  }
  const toggleSection = (sectionId: string) =>
    setOpenSections(prev => {
      const next = new Set(prev)
      if (next.has(sectionId)) next.delete(sectionId)
      else next.add(sectionId)
      return next
    })

  const invalidSections = useMemo(
    () => new Set((validation?.missing_fields ?? []).map(f => f.section)),
    [validation],
  )

  if (isEdit && programQ.isLoading) return <EditorSkeleton />

  const isOpen = (sid: string) => openSections.has(sid)
  const idx = (sid: SectionId) => SECTIONS.findIndex(s => s.id === sid) + 1

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      {/* Sticky header */}
      <div className="sticky top-0 z-20 -mx-4 mb-6 border-b border-border bg-background/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/i/programs')}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Back to programs"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <h1 className="text-h3 font-semibold text-foreground">
                {isEdit ? draft.program_name || 'Edit program' : 'New program'}
              </h1>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant={published ? 'success' : 'neutral'}>
                  {published ? 'Published' : 'Draft'}
                </Badge>
                {isEdit && baselineVersion != null && <span>Version {baselineVersion}</span>}
                {isEdit && appsCount > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <Layers size={12} /> {appsCount} application{appsCount === 1 ? '' : 's'} reference
                    this program
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isEdit && published && (
              <Button variant="tertiary" size="sm" onClick={() => unpublishMut.mutate()} disabled={saving}>
                <EyeOff size={15} /> Unpublish
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onSaveDraft} disabled={saving} loading={updateMut.isPending || createMut.isPending}>
              <Save size={15} /> Save draft
            </Button>
            <Button variant="secondary" size="sm" onClick={onPublish} disabled={saving} loading={publishMut.isPending}>
              <Send size={15} /> {published ? 'Republish' : 'Publish program'}
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_200px]">
        {/* Sections */}
        <div className="space-y-4">
          {/* 01 · Identity */}
          <SectionCard id="identity" index={idx('identity')} title="Identity" open={isOpen('identity')} onToggle={() => toggleSection('identity')} invalid={invalidSections.has('identity')}>
            <Input label="Program name" required value={draft.program_name} onChange={e => set('program_name', e.target.value)} placeholder="e.g. Computer Science, M.S." />
            <div className="grid gap-4 sm:grid-cols-2">
              <Select label="Degree type" required options={DEGREE_OPTIONS} placeholder="Select degree" value={draft.degree_type} onChange={e => set('degree_type', e.target.value)} />
              <Select label="Sub-school / college" options={schoolOptions} value={draft.school_id} onChange={e => set('school_id', e.target.value)} helperText={schoolOptions.length <= 1 ? 'Add schools in Settings to group programs.' : undefined} />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Department" value={draft.department} onChange={e => set('department', e.target.value)} placeholder="e.g. Engineering" />
              <Select label="Delivery format" options={DELIVERY_FORMAT_OPTIONS} value={draft.delivery_format} onChange={e => set('delivery_format', e.target.value)} />
              <Input label="Duration (months)" type="number" min={1} value={draft.duration_months} onChange={e => set('duration_months', e.target.value)} placeholder="e.g. 24" />
            </div>
            <Select label="Campus setting" options={CAMPUS_SETTING_OPTIONS} value={draft.campus_setting} onChange={e => set('campus_setting', e.target.value)} />
          </SectionCard>

          {/* 02 · Overview & structure */}
          <SectionCard id="overview" index={idx('overview')} title="Overview & structure" open={isOpen('overview')} onToggle={() => toggleSection('overview')} invalid={invalidSections.has('overview')}>
            <Textarea label="Description (markdown)" value={draft.description_text} onChange={e => set('description_text', e.target.value)} rows={6} placeholder="Describe the program, its academic focus, and what makes it distinctive…" helperText="Plain markdown. This is the lead of the student Overview tab." />
            <div>
              <MiniLabel>Tracks / concentrations</MiniLabel>
              <ChipsInput values={draft.tracks_concentrations} onChange={v => set('tracks_concentrations', v)} placeholder="Type a track and press Enter" />
            </div>
            <Input label="Concentration note (optional)" value={draft.tracks_note} onChange={e => set('tracks_note', e.target.value)} placeholder='e.g. "Choose one of 5 concentrations in year 2"' />
            <Textarea label="Learning-format expectations" value={draft.learning_format} onChange={e => set('learning_format', e.target.value)} rows={3} placeholder="Cohort vs. self-paced, in-person residency requirements, weekly time commitment…" />
            <Textarea label="Who it's for" value={draft.who_its_for} onChange={e => set('who_its_for', e.target.value)} rows={3} placeholder="Describe the ideal candidate for this program…" />
            <div>
              <MiniLabel>Highlights</MiniLabel>
              <ChipsInput values={draft.highlights} onChange={v => set('highlights', v)} placeholder="e.g. STEM-designated · press Enter" />
            </div>
            <div>
              <MiniLabel>Faculty contacts</MiniLabel>
              <Repeatable
                items={draft.faculty_contacts}
                addLabel="Add contact"
                emptyHint="No faculty contacts added."
                onAdd={() => set('faculty_contacts', [...draft.faculty_contacts, { name: '', email: '', role: '' }])}
                onRemove={i => set('faculty_contacts', draft.faculty_contacts.filter((_, x) => x !== i))}
                renderRow={(c, i) => (
                  <div className="grid gap-2 sm:grid-cols-3">
                    <Input value={c.name} onChange={e => set('faculty_contacts', draft.faculty_contacts.map((f, x) => (x === i ? { ...f, name: e.target.value } : f)))} placeholder="Name" />
                    <Input value={c.email} onChange={e => set('faculty_contacts', draft.faculty_contacts.map((f, x) => (x === i ? { ...f, email: e.target.value } : f)))} placeholder="Email" />
                    <Input value={c.role} onChange={e => set('faculty_contacts', draft.faculty_contacts.map((f, x) => (x === i ? { ...f, role: e.target.value } : f)))} placeholder="Role" />
                  </div>
                )}
              />
            </div>
          </SectionCard>

          {/* 03 · Requirements */}
          <SectionCard
            id="requirements"
            index={idx('requirements')}
            title="Requirements"
            open={isOpen('requirements')}
            onToggle={() => toggleSection('requirements')}
            invalid={invalidSections.has('requirements')}
            crossLink={{ label: 'Manage application checklist', to: '/i/requirements' }}
            rawValue={draft.application_requirements}
            onApplyRaw={parsed => parsed && setReqs(parsed)}
          >
            <div>
              <MiniLabel>Application materials</MiniLabel>
              <Repeatable
                items={draft.application_requirements.materials}
                addLabel="Add material"
                emptyHint="No materials yet. Add transcripts, essays, portfolio, etc."
                onAdd={() => setReqs({ materials: [...draft.application_requirements.materials, { name: '', required: true }] })}
                onRemove={i => setReqs({ materials: draft.application_requirements.materials.filter((_, x) => x !== i) })}
                renderRow={(m, i) => (
                  <div className="flex flex-wrap items-center gap-2">
                    <Input className="flex-1 min-w-[12rem]" value={m.name} onChange={e => setReqs({ materials: draft.application_requirements.materials.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })} placeholder="e.g. Statement of purpose" />
                    <Toggle checked={m.required} onChange={v => setReqs({ materials: draft.application_requirements.materials.map((x, j) => (j === i ? { ...x, required: v } : x)) })} label="Required" />
                  </div>
                )}
              />
            </div>

            <div>
              <MiniLabel>Prerequisites</MiniLabel>
              <Repeatable
                items={draft.application_requirements.prerequisites}
                addLabel="Add prerequisite"
                emptyHint="No prerequisites."
                onAdd={() => setReqs({ prerequisites: [...draft.application_requirements.prerequisites, { name: '', required: true, allowed_substitutes: [] }] })}
                onRemove={i => setReqs({ prerequisites: draft.application_requirements.prerequisites.filter((_, x) => x !== i) })}
                renderRow={(p, i) => (
                  <div className="space-y-2 rounded-md border border-border bg-muted/30 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Input className="flex-1 min-w-[12rem]" value={p.name} onChange={e => setReqs({ prerequisites: draft.application_requirements.prerequisites.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })} placeholder="e.g. Calculus I–III" />
                      <Toggle checked={p.required} onChange={v => setReqs({ prerequisites: draft.application_requirements.prerequisites.map((x, j) => (j === i ? { ...x, required: v } : x)) })} label="Required" />
                    </div>
                    <ChipsInput values={p.allowed_substitutes} onChange={v => setReqs({ prerequisites: draft.application_requirements.prerequisites.map((x, j) => (j === i ? { ...x, allowed_substitutes: v } : x)) })} placeholder="Allowed substitutes · press Enter" />
                  </div>
                )}
              />
            </div>

            <div className="space-y-3 rounded-md border border-border p-4">
              <MiniLabel>Test policy</MiniLabel>
              <div className="grid gap-4 sm:grid-cols-2">
                <Select label="Stance" options={TEST_STANCE_OPTIONS} value={draft.application_requirements.test_policy.stance} onChange={e => setTestPolicy({ stance: e.target.value as any })} />
                <Input label="Selectivity — acceptance rate (%)" type="number" min={0} max={100} value={draft.acceptance_rate_pct} onChange={e => set('acceptance_rate_pct', e.target.value)} placeholder="e.g. 12" />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <MiniLabel>Required tests</MiniLabel>
                  <ChipsInput values={draft.application_requirements.test_policy.required} onChange={v => setTestPolicy({ required: v })} placeholder="e.g. GRE · press Enter" />
                </div>
                <div>
                  <MiniLabel>Optional tests</MiniLabel>
                  <ChipsInput values={draft.application_requirements.test_policy.optional} onChange={v => setTestPolicy({ optional: v })} placeholder="e.g. GMAT · press Enter" />
                </div>
              </div>
              <div>
                <MiniLabel>Accepted tests</MiniLabel>
                <ChipsInput values={draft.application_requirements.test_policy.accepted_tests} onChange={v => setTestPolicy({ accepted_tests: v })} placeholder="e.g. GRE, GMAT" />
              </div>
              <Toggle checked={draft.application_requirements.test_policy.superscore_enabled} onChange={v => setTestPolicy({ superscore_enabled: v })} label="Superscore across attempts" />
              <Input label="Waiver rules" value={draft.application_requirements.test_policy.waived_rules} onChange={e => setTestPolicy({ waived_rules: e.target.value })} placeholder="e.g. Waived for 3+ years professional experience" />
              <div>
                <MiniLabel>Typical score ranges</MiniLabel>
                <Repeatable
                  items={draft.application_requirements.test_policy.typical_ranges}
                  addLabel="Add range"
                  emptyHint="No typical ranges published."
                  onAdd={() => setTestPolicy({ typical_ranges: [...draft.application_requirements.test_policy.typical_ranges, { test: '', low: 0, high: 0 }] })}
                  onRemove={i => setTestPolicy({ typical_ranges: draft.application_requirements.test_policy.typical_ranges.filter((_, x) => x !== i) })}
                  renderRow={(t, i) => (
                    <div className="grid gap-2 sm:grid-cols-3">
                      <Input value={t.test} onChange={e => setTestPolicy({ typical_ranges: draft.application_requirements.test_policy.typical_ranges.map((x, j) => (j === i ? { ...x, test: e.target.value } : x)) })} placeholder="Test" />
                      <Input type="number" value={String(t.low)} onChange={e => setTestPolicy({ typical_ranges: draft.application_requirements.test_policy.typical_ranges.map((x, j) => (j === i ? { ...x, low: Number(e.target.value) } : x)) })} placeholder="Low" />
                      <Input type="number" value={String(t.high)} onChange={e => setTestPolicy({ typical_ranges: draft.application_requirements.test_policy.typical_ranges.map((x, j) => (j === i ? { ...x, high: Number(e.target.value) } : x)) })} placeholder="High" />
                    </div>
                  )}
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Recommendations required" type="number" min={0} value={String(draft.application_requirements.recommendations.required_count)} onChange={e => setReqs({ recommendations: { ...draft.application_requirements.recommendations, required_count: Number(e.target.value) || 0 } })} />
              <div>
                <MiniLabel>Recommendation types</MiniLabel>
                <div className="flex flex-wrap gap-3 pt-1.5">
                  {REC_TYPE_OPTIONS.map(o => {
                    const on = draft.application_requirements.recommendations.types.includes(o.value)
                    return (
                      <Toggle key={o.value} label={o.label} checked={on} onChange={v => setReqs({ recommendations: { ...draft.application_requirements.recommendations, types: v ? [...draft.application_requirements.recommendations.types, o.value] : draft.application_requirements.recommendations.types.filter(t => t !== o.value) } })} />
                    )
                  })}
                </div>
              </div>
            </div>

            <div>
              <MiniLabel>Other academic requirements (key / value)</MiniLabel>
              <Repeatable
                items={draft.requirements_kv}
                addLabel="Add requirement"
                emptyHint="e.g. min_gpa → 3.0"
                onAdd={() => set('requirements_kv', [...draft.requirements_kv, { key: '', value: '' }])}
                onRemove={i => set('requirements_kv', draft.requirements_kv.filter((_, x) => x !== i))}
                renderRow={(r, i) => (
                  <div className="flex gap-2">
                    <Input className="w-44" value={r.key} onChange={e => set('requirements_kv', draft.requirements_kv.map((x, j) => (j === i ? { ...x, key: e.target.value } : x)))} placeholder="Key" />
                    <Input className="flex-1" value={r.value} onChange={e => set('requirements_kv', draft.requirements_kv.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)))} placeholder="Value" />
                  </div>
                )}
              />
            </div>
          </SectionCard>

          {/* 04 · English proficiency (Spec 38 §2.2) */}
          <SectionCard
            id="english"
            index={idx('english')}
            title="English proficiency"
            description="Accepted English tests + minimum scores for international applicants, plus waiver rules. Used by the international-admissions workspace."
            open={isOpen('english')}
            onToggle={() => toggleSection('english')}
            invalid={invalidSections.has('english')}
            rawValue={draft.english_policy}
            onApplyRaw={parsed =>
              parsed && setDraft(d => ({ ...d, english_policy: { ...d.english_policy, ...parsed } }))
            }
          >
            <div>
              <MiniLabel>Accepted tests &amp; minimum scores</MiniLabel>
              <Repeatable
                items={draft.english_policy.accepted_tests}
                addLabel="Add test"
                emptyHint="e.g. TOEFL → 100, IELTS → 7.0"
                onAdd={() =>
                  setEnglish({
                    accepted_tests: [
                      ...draft.english_policy.accepted_tests,
                      { test: 'TOEFL', min_score: '' },
                    ],
                  })
                }
                onRemove={i =>
                  setEnglish({
                    accepted_tests: draft.english_policy.accepted_tests.filter((_, x) => x !== i),
                  })
                }
                renderRow={(t, i) => (
                  <div className="flex gap-2">
                    <div className="w-44">
                      <Select
                        options={ENGLISH_TEST_OPTIONS}
                        value={t.test}
                        onChange={e =>
                          setEnglish({
                            accepted_tests: draft.english_policy.accepted_tests.map((x, j) =>
                              j === i ? { ...x, test: e.target.value } : x,
                            ),
                          })
                        }
                      />
                    </div>
                    <Input
                      className="flex-1"
                      type="number"
                      value={t.min_score}
                      onChange={e =>
                        setEnglish({
                          accepted_tests: draft.english_policy.accepted_tests.map((x, j) =>
                            j === i ? { ...x, min_score: e.target.value } : x,
                          ),
                        })
                      }
                      placeholder="Min score"
                    />
                  </div>
                )}
              />
            </div>
            <div>
              <MiniLabel>Native-English-country waiver list</MiniLabel>
              <ChipsInput
                values={draft.english_policy.waiver_native_english_countries}
                onChange={v => setEnglish({ waiver_native_english_countries: v })}
                placeholder="e.g. US, GB, AU · press Enter"
              />
            </div>
            <Toggle
              checked={draft.english_policy.waiver_prior_degree_in_english}
              onChange={v => setEnglish({ waiver_prior_degree_in_english: v })}
              label="Waive for a prior degree completed in English"
            />
          </SectionCard>

          {/* 04 · Deadlines & rounds */}
          <SectionCard
            id="deadlines"
            index={idx('deadlines')}
            title="Deadlines & rounds"
            open={isOpen('deadlines')}
            onToggle={() => toggleSection('deadlines')}
            invalid={invalidSections.has('deadlines')}
            crossLink={{ label: 'Open intake rounds manager', to: '/i/intake-rounds' }}
            rawValue={draft.intake_rounds}
            onApplyRaw={parsed => Array.isArray(parsed) && set('intake_rounds', parsed)}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Primary application deadline" type="date" value={draft.application_deadline} onChange={e => set('application_deadline', e.target.value)} helperText="Shown as the headline deadline when no rounds are set." />
              <Input label="Program start date" type="date" value={draft.program_start_date} onChange={e => set('program_start_date', e.target.value)} />
            </div>
            <Repeatable
              items={draft.intake_rounds}
              addLabel="Add intake round"
              emptyHint="No rounds yet. Add rounds for multi-deadline admissions (e.g. Round 1 / Round 2)."
              onAdd={() => set('intake_rounds', [...draft.intake_rounds, emptyRound()])}
              onRemove={i => set('intake_rounds', draft.intake_rounds.filter((_, x) => x !== i))}
              renderRow={(r, i) => (
                <div className="space-y-2 rounded-md border border-border bg-muted/30 p-3">
                  <div className="grid gap-2 sm:grid-cols-3">
                    <Input value={r.name} onChange={e => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} placeholder="Round name" />
                    <Input value={r.term.season} onChange={e => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, term: { ...x.term, season: e.target.value } } : x)))} placeholder="Season (e.g. Fall)" />
                    <Input type="number" value={String(r.term.year)} onChange={e => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, term: { ...x.term, year: Number(e.target.value) || x.term.year } } : x)))} placeholder="Year" />
                  </div>
                  <div className="grid gap-2 sm:grid-cols-5">
                    <DateField label="Opens" value={r.open_date} onChange={v => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, open_date: v } : x)))} />
                    <DateField label="Deadline" value={r.deadline} onChange={v => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, deadline: v } : x)))} />
                    <DateField label="Decision" value={r.decision_date} onChange={v => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, decision_date: v } : x)))} />
                    <DateField label="Start" value={r.start_date} onChange={v => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, start_date: v } : x)))} />
                    <Input label="Capacity" type="number" value={r.capacity != null ? String(r.capacity) : ''} onChange={e => set('intake_rounds', draft.intake_rounds.map((x, j) => (j === i ? { ...x, capacity: e.target.value ? Number(e.target.value) : null } : x)))} placeholder="—" />
                  </div>
                </div>
              )}
            />
          </SectionCard>

          {/* 05 · Costs */}
          <SectionCard
            id="costs"
            index={idx('costs')}
            title="Costs"
            open={isOpen('costs')}
            onToggle={() => toggleSection('costs')}
            invalid={invalidSections.has('costs')}
            rawValue={draft.cost_data}
            onApplyRaw={parsed => parsed && setCost(parsed)}
          >
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Tuition amount" type="number" min={0} value={draft.cost_data.tuition_amount != null ? String(draft.cost_data.tuition_amount) : ''} onChange={e => setCost({ tuition_amount: e.target.value ? Number(e.target.value) : null })} placeholder="e.g. 48000" />
              <Input label="Currency" value={draft.cost_data.tuition_currency} onChange={e => setCost({ tuition_currency: e.target.value.toUpperCase() })} placeholder="USD" />
              <Select label="Period" options={TUITION_PERIOD_OPTIONS} value={draft.cost_data.tuition_period} onChange={e => setCost({ tuition_period: e.target.value as any })} />
            </div>
            <div>
              <MiniLabel>Fees</MiniLabel>
              <Repeatable
                items={draft.cost_data.fees}
                addLabel="Add fee"
                emptyHint="No fees added."
                onAdd={() => setCost({ fees: [...draft.cost_data.fees, { name: '', amount: 0, required: true }] })}
                onRemove={i => setCost({ fees: draft.cost_data.fees.filter((_, x) => x !== i) })}
                renderRow={(f, i) => (
                  <div className="flex flex-wrap items-center gap-2">
                    <Input className="flex-1 min-w-[10rem]" value={f.name} onChange={e => setCost({ fees: draft.cost_data.fees.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })} placeholder="Fee name" />
                    <Input className="w-32" type="number" value={String(f.amount)} onChange={e => setCost({ fees: draft.cost_data.fees.map((x, j) => (j === i ? { ...x, amount: Number(e.target.value) || 0 } : x)) })} placeholder="Amount" />
                    <Toggle checked={f.required} onChange={v => setCost({ fees: draft.cost_data.fees.map((x, j) => (j === i ? { ...x, required: v } : x)) })} label="Required" />
                  </div>
                )}
              />
            </div>
            <div>
              <MiniLabel>Estimated total cost band</MiniLabel>
              <div className="grid gap-2 sm:grid-cols-3">
                <Input type="number" value={draft.cost_data.estimated_total_cost_band.min != null ? String(draft.cost_data.estimated_total_cost_band.min) : ''} onChange={e => setCost({ estimated_total_cost_band: { ...draft.cost_data.estimated_total_cost_band, min: e.target.value ? Number(e.target.value) : null } })} placeholder="Min" />
                <Input type="number" value={draft.cost_data.estimated_total_cost_band.max != null ? String(draft.cost_data.estimated_total_cost_band.max) : ''} onChange={e => setCost({ estimated_total_cost_band: { ...draft.cost_data.estimated_total_cost_band, max: e.target.value ? Number(e.target.value) : null } })} placeholder="Max" />
                <Input value={draft.cost_data.estimated_total_cost_band.currency} onChange={e => setCost({ estimated_total_cost_band: { ...draft.cost_data.estimated_total_cost_band, currency: e.target.value.toUpperCase() } })} placeholder="Currency" />
              </div>
            </div>
            <div>
              <MiniLabel>Funding signals</MiniLabel>
              <div className="grid gap-3 pt-1 sm:grid-cols-2">
                <Toggle checked={draft.cost_data.funding_signals.ta_funded} onChange={v => setCost({ funding_signals: { ...draft.cost_data.funding_signals, ta_funded: v } })} label="TA funding available" />
                <Toggle checked={draft.cost_data.funding_signals.ra_funded} onChange={v => setCost({ funding_signals: { ...draft.cost_data.funding_signals, ra_funded: v } })} label="RA funding available" />
                <Toggle checked={draft.cost_data.funding_signals.merit_scholarship_available} onChange={v => setCost({ funding_signals: { ...draft.cost_data.funding_signals, merit_scholarship_available: v } })} label="Merit scholarships" />
                <Toggle checked={draft.cost_data.funding_signals.need_based_available} onChange={v => setCost({ funding_signals: { ...draft.cost_data.funding_signals, need_based_available: v } })} label="Need-based aid" />
              </div>
            </div>
          </SectionCard>

          {/* 06 · Outcomes */}
          <SectionCard
            id="outcomes"
            index={idx('outcomes')}
            title="Outcomes"
            open={isOpen('outcomes')}
            onToggle={() => toggleSection('outcomes')}
            invalid={invalidSections.has('outcomes')}
            rawValue={draft.outcomes_data}
            onApplyRaw={parsed => parsed && setOutcomes(parsed)}
          >
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Placement rate (%)" type="number" min={0} max={100} value={draft.outcomes_data.placement_rate_pct != null ? String(draft.outcomes_data.placement_rate_pct) : ''} onChange={e => setOutcomes({ placement_rate_pct: e.target.value ? Number(e.target.value) : null })} placeholder="e.g. 94" />
              <Input label="Median starting salary" type="number" min={0} value={draft.outcomes_data.median_starting_salary != null ? String(draft.outcomes_data.median_starting_salary) : ''} onChange={e => setOutcomes({ median_starting_salary: e.target.value ? Number(e.target.value) : null })} placeholder="e.g. 95000" />
              <Input label="Internship→offer (%)" type="number" min={0} max={100} value={draft.outcomes_data.internship_to_offer_pct != null ? String(draft.outcomes_data.internship_to_offer_pct) : ''} onChange={e => setOutcomes({ internship_to_offer_pct: e.target.value ? Number(e.target.value) : null })} placeholder="e.g. 80" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Time to placement (months)" type="number" min={0} value={draft.outcomes_data.time_to_placement_months != null ? String(draft.outcomes_data.time_to_placement_months) : ''} onChange={e => setOutcomes({ time_to_placement_months: e.target.value ? Number(e.target.value) : null })} placeholder="e.g. 4" />
              <Input label="Reporting window" value={draft.outcomes_data.outcome_reporting_window} onChange={e => setOutcomes({ outcome_reporting_window: e.target.value })} placeholder="e.g. Within 6 months of graduation (Class of 2024)" />
            </div>
            <div>
              <MiniLabel>Common roles</MiniLabel>
              <ChipsInput values={draft.outcomes_data.common_roles} onChange={v => setOutcomes({ common_roles: v })} placeholder="e.g. Software Engineer · press Enter" />
            </div>
            <div>
              <MiniLabel>Top employers</MiniLabel>
              <ChipsInput values={draft.outcomes_data.top_employers} onChange={v => setOutcomes({ top_employers: v })} placeholder="e.g. Google, Microsoft" />
            </div>
            <div>
              <MiniLabel>Salary distribution bands</MiniLabel>
              <Repeatable
                items={draft.outcomes_data.salary_distribution_bands}
                addLabel="Add band"
                emptyHint="No distribution bands."
                onAdd={() => setOutcomes({ salary_distribution_bands: [...draft.outcomes_data.salary_distribution_bands, { band_label: '', percent: 0 }] })}
                onRemove={i => setOutcomes({ salary_distribution_bands: draft.outcomes_data.salary_distribution_bands.filter((_, x) => x !== i) })}
                renderRow={(b, i) => (
                  <div className="flex gap-2">
                    <Input className="flex-1" value={b.band_label} onChange={e => setOutcomes({ salary_distribution_bands: draft.outcomes_data.salary_distribution_bands.map((x, j) => (j === i ? { ...x, band_label: e.target.value } : x)) })} placeholder="e.g. $80k–$100k" />
                    <Input className="w-28" type="number" value={String(b.percent)} onChange={e => setOutcomes({ salary_distribution_bands: draft.outcomes_data.salary_distribution_bands.map((x, j) => (j === i ? { ...x, percent: Number(e.target.value) || 0 } : x)) })} placeholder="% " />
                  </div>
                )}
              />
            </div>
          </SectionCard>

          {/* 07 · Media */}
          <SectionCard id="media" index={idx('media')} title="Media" open={isOpen('media')} onToggle={() => toggleSection('media')} invalid={invalidSections.has('media')}>
            <div className="rounded-md border border-secondary/30 bg-secondary/5 p-3 text-sm text-foreground">
              <p className="font-semibold">Program logo is text-only.</p>
              <p className="text-muted-foreground">
                Per brand, program pages are editorial — no decorative imagery, gradients, or marketing
                photography. The wordmark renders from your program name automatically. Use the optional
                gallery only for genuinely informative assets.
              </p>
            </div>
            <div>
              <MiniLabel>Optional gallery URLs</MiniLabel>
              <Repeatable
                items={draft.media_urls}
                addLabel="Add URL"
                emptyHint="No media. This is optional and rarely needed."
                onAdd={() => set('media_urls', [...draft.media_urls, ''])}
                onRemove={i => set('media_urls', draft.media_urls.filter((_, x) => x !== i))}
                renderRow={(u, i) => (
                  <Input value={u} onChange={e => set('media_urls', draft.media_urls.map((x, j) => (j === i ? e.target.value : x)))} placeholder="https://…" />
                )}
              />
            </div>
          </SectionCard>

          {/* 08 · Promotion settings */}
          <SectionCard id="promotion" index={idx('promotion')} title="Promotion settings" open={isOpen('promotion')} onToggle={() => toggleSection('promotion')} invalid={invalidSections.has('promotion')} crossLink={{ label: 'Manage promoted placements', to: '/i/promotions' }}>
            <p className="text-sm text-muted-foreground">
              Categories this program opts into for promoted placements. The actual promoted campaigns and
              budget run in Promotions.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              {PROMOTION_CATEGORY_OPTIONS.map(o => {
                const on = draft.promotion_categories.includes(o.value)
                return (
                  <Toggle key={o.value} label={o.label} checked={on} onChange={v => set('promotion_categories', v ? [...draft.promotion_categories, o.value] : draft.promotion_categories.filter(c => c !== o.value))} />
                )
              })}
            </div>
          </SectionCard>
        </div>

        {/* On-this-page rail */}
        <nav className="hidden lg:block">
          <div className="sticky top-24 space-y-1">
            <p className="px-2 pb-1 text-eyebrow uppercase tracking-[0.22em] text-muted-foreground">On this page</p>
            {SECTIONS.map(s => (
              <button
                key={s.id}
                type="button"
                onClick={() => goToSection(s.id)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <span className="text-xs tabular-nums text-secondary">{String(idx(s.id)).padStart(2, '0')}</span>
                {s.label}
                {invalidSections.has(s.id) && <AlertTriangle size={13} className="text-error" />}
              </button>
            ))}
          </div>
        </nav>
      </div>

      {/* Publish validation modal (Spec 23 §6) */}
      <Modal
        isOpen={!!validation}
        onClose={() => setValidation(null)}
        title="Resolve before publishing"
        footer={<Button variant="secondary" onClick={() => setValidation(null)}>Got it</Button>}
      >
        <p className="mb-3 text-sm text-foreground">{validation?.message}</p>
        <ul className="space-y-2">
          {(validation?.missing_fields ?? []).map((f, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => {
                  setValidation(null)
                  goToSection(f.section)
                }}
                className="flex w-full items-center gap-2 rounded-md border border-border px-3 py-2 text-left text-sm hover:border-secondary hover:bg-secondary/5"
              >
                <AlertTriangle size={15} className="shrink-0 text-warning" />
                <span className="text-foreground">{f.message}</span>
                <span className="ml-auto text-xs text-secondary">Go to {SECTIONS.find(s => s.id === f.section)?.label ?? f.section} →</span>
              </button>
            </li>
          ))}
        </ul>
      </Modal>

      {/* Concurrent-edit conflict modal (Spec 23 §6) */}
      <Modal
        isOpen={conflict}
        onClose={() => setConflict(false)}
        title="Someone else edited this"
        footer={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setConflict(false)}>Keep editing</Button>
            <Button
              variant="secondary"
              onClick={() => {
                setConflict(false)
                loadedRef.current = false
                programQ.refetch()
              }}
            >
              Reload their changes
            </Button>
          </div>
        }
      >
        <p className="text-sm text-foreground">
          This program was changed by someone else since you opened it. Reload to see their changes
          (your unsaved edits will be replaced), or keep editing and save again to retry.
        </p>
      </Modal>
    </div>
  )
}

function DateField({ label, value, onChange }: { label: string; value: string | null; onChange: (v: string | null) => void }) {
  return (
    <Input
      label={label}
      type="date"
      value={value ? String(value).split('T')[0] : ''}
      onChange={e => onChange(e.target.value || null)}
    />
  )
}

function EditorSkeleton() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <Skeleton className="h-8 w-64" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-32" />
        </div>
      </div>
      <div className="space-y-4">
        {[0, 1, 2, 3].map(i => (
          <Card key={i} className="p-6">
            <Skeleton className="mb-4 h-6 w-40" />
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
