import { useForm } from 'react-hook-form'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Textarea from '../../../components/ui/Textarea'
import Select from '../../../components/ui/Select'
import { DEGREE_LABELS, TEST_TYPES, ACTIVITY_TYPES, GPA_SCALES, CITY_SIZE_OPTIONS, FUNDING_OPTIONS, PLATFORM_TYPES, PORTFOLIO_ITEM_TYPES, RESEARCH_ROLES, RESEARCH_OUTPUTS, PROFICIENCY_LEVELS, WORK_EXPERIENCE_TYPES, COMPENSATION_TYPES, COMPETITION_LEVELS, ACCOMMODATION_CATEGORIES, DOC_STATUS_OPTIONS, FONT_SIZE_OPTIONS, INTERVIEW_FORMAT_OPTIONS, SPONSORSHIP_SOURCES } from '../../../utils/constants'

interface FormProps {
  defaultValues: any
  onSubmit: (d: any) => void
  loading: boolean
}

export function BasicInfoForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { first_name: defaultValues?.first_name || '', last_name: defaultValues?.last_name || '', date_of_birth: defaultValues?.date_of_birth?.slice(0, 10) || '', nationality: defaultValues?.nationality || '', country_of_residence: defaultValues?.country_of_residence || '', bio_text: defaultValues?.bio_text || '', goals_text: defaultValues?.goals_text || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Input label="First Name" {...register('first_name')} />
        <Input label="Last Name" {...register('last_name')} />
      </div>
      <Input label="Date of Birth" type="date" {...register('date_of_birth')} />
      <Input label="Nationality" {...register('nationality')} />
      <Input label="Country of Residence" {...register('country_of_residence')} />
      <Textarea label="Bio" {...register('bio_text')} />
      <Textarea label="Goals" {...register('goals_text')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function AcademicForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { institution_name: defaultValues?.institution_name || '', degree_type: defaultValues?.degree_type || 'bachelors', field_of_study: defaultValues?.field_of_study || '', gpa: defaultValues?.gpa || '', gpa_scale: defaultValues?.gpa_scale || '4.0', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false, country: defaultValues?.country || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, gpa: d.gpa ? Number(d.gpa) : null }))} className="space-y-3">
      <Input label="Institution Name" {...register('institution_name')} />
      <Select label="Degree Type" options={Object.entries(DEGREE_LABELS).map(([v, l]) => ({ value: v, label: l }))} {...register('degree_type')} />
      <Input label="Field of Study" {...register('field_of_study')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="GPA" type="number" step="0.01" {...register('gpa')} />
        <Select label="GPA Scale" options={GPA_SCALES} {...register('gpa_scale')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <Input label="Country" {...register('country')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function TestScoreForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { test_type: defaultValues?.test_type || 'SAT', total_score: defaultValues?.total_score || '', test_date: defaultValues?.test_date?.slice(0, 10) || '', is_official: defaultValues?.is_official || false } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, total_score: d.total_score ? Number(d.total_score) : null }))} className="space-y-3">
      <Select label="Test Type" options={TEST_TYPES.map(t => ({ value: t, label: t }))} {...register('test_type')} />
      <Input label="Total Score" type="number" {...register('total_score')} />
      <Input label="Test Date" type="date" {...register('test_date')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('is_official')} /> Official Score</label>
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function ActivityForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { activity_type: defaultValues?.activity_type || 'extracurricular', title: defaultValues?.title || '', organization: defaultValues?.organization || '', description: defaultValues?.description || '', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false, hours_per_week: defaultValues?.hours_per_week || '', impact_description: defaultValues?.impact_description || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, hours_per_week: d.hours_per_week ? Number(d.hours_per_week) : null }))} className="space-y-3">
      <Select label="Type" options={ACTIVITY_TYPES} {...register('activity_type')} />
      <Input label="Title" {...register('title')} />
      <Input label="Organization" {...register('organization')} />
      <Textarea label="Description" {...register('description')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <Input label="Hours/Week" type="number" {...register('hours_per_week')} />
      <Textarea label="Impact" {...register('impact_description')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function PreferencesForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { preferred_countries: defaultValues?.preferred_countries?.join(', ') || '', preferred_city_size: defaultValues?.preferred_city_size || '', budget_min: defaultValues?.budget_min || '', budget_max: defaultValues?.budget_max || '', funding_requirement: defaultValues?.funding_requirement || '', goals_text: defaultValues?.goals_text || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, preferred_countries: d.preferred_countries ? d.preferred_countries.split(',').map((s: string) => s.trim()).filter(Boolean) : [], budget_min: d.budget_min ? Number(d.budget_min) : null, budget_max: d.budget_max ? Number(d.budget_max) : null }))} className="space-y-3">
      <Input label="Preferred Countries (comma-separated)" {...register('preferred_countries')} />
      <Select label="City Size" options={CITY_SIZE_OPTIONS} placeholder="Select..." {...register('preferred_city_size')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Budget Min ($)" type="number" {...register('budget_min')} />
        <Input label="Budget Max ($)" type="number" {...register('budget_max')} />
      </div>
      <Select label="Funding Requirement" options={FUNDING_OPTIONS} placeholder="Select..." {...register('funding_requirement')} />
      <Textarea label="Goals" {...register('goals_text')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function OnlinePresenceForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { platform_type: defaultValues?.platform_type || 'linkedin', url: defaultValues?.url || '', display_name: defaultValues?.display_name || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Select label="Platform" options={PLATFORM_TYPES} {...register('platform_type')} />
      <Input label="URL" type="url" placeholder="https://..." {...register('url')} />
      <Input label="Display Name (optional)" placeholder="My Portfolio" {...register('display_name')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function PortfolioItemForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { title: defaultValues?.title || '', description: defaultValues?.description || '', item_type: defaultValues?.item_type || 'project', url: defaultValues?.url || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Title" placeholder="My capstone project" {...register('title')} />
      <Select label="Type" options={PORTFOLIO_ITEM_TYPES} {...register('item_type')} />
      <Input label="URL (optional)" type="url" placeholder="https://..." {...register('url')} />
      <Textarea label="Description (optional)" placeholder="Brief description of this work..." {...register('description')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function ResearchForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { title: defaultValues?.title || '', institution_lab: defaultValues?.institution_lab || '', field_discipline: defaultValues?.field_discipline || '', role: defaultValues?.role || 'assistant', advisor_name: defaultValues?.advisor_name || '', methods_tools: defaultValues?.methods_tools || '', outcomes: defaultValues?.outcomes || '', outputs: defaultValues?.outputs || 'none', publication_link: defaultValues?.publication_link || '', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Research Title" placeholder="NLP for educational matching" {...register('title')} />
      <Input label="Lab / Institution" placeholder="MIT CSAIL" {...register('institution_lab')} />
      <div className="grid grid-cols-2 gap-3">
        <Select label="Role" options={RESEARCH_ROLES} {...register('role')} />
        <Input label="Field" placeholder="Computer Science" {...register('field_discipline')} />
      </div>
      <Input label="Advisor" placeholder="Prof. Smith" {...register('advisor_name')} />
      <Textarea label="Methods / Tools" placeholder="Python, PyTorch, transformers..." {...register('methods_tools')} />
      <Textarea label="Outcomes" placeholder="Findings and contributions..." {...register('outcomes')} />
      <div className="grid grid-cols-2 gap-3">
        <Select label="Output" options={RESEARCH_OUTPUTS} {...register('outputs')} />
        <Input label="Publication Link" type="url" placeholder="https://..." {...register('publication_link')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('is_current')} /> Currently active</label>
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function LanguageForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { language: defaultValues?.language || '', proficiency_level: defaultValues?.proficiency_level || 'intermediate', certification_type: defaultValues?.certification_type || '', certification_score: defaultValues?.certification_score || '', test_date: defaultValues?.test_date?.slice(0, 10) || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Language" placeholder="English, Mandarin, Spanish..." {...register('language')} />
      <Select label="Proficiency" options={PROFICIENCY_LEVELS} {...register('proficiency_level')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Certification (optional)" placeholder="TOEFL, IELTS..." {...register('certification_type')} />
        <Input label="Score (optional)" placeholder="110, 7.5..." {...register('certification_score')} />
      </div>
      <Input label="Test Date (optional)" type="date" {...register('test_date')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function WorkExperienceForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { experience_type: defaultValues?.experience_type || 'employment', organization: defaultValues?.organization || '', role_title: defaultValues?.role_title || '', description: defaultValues?.description || '', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false, hours_per_week: defaultValues?.hours_per_week || '', compensation_type: defaultValues?.compensation_type || '', key_achievements: defaultValues?.key_achievements || '', supervisor_name: defaultValues?.supervisor_name || '', organization_country: defaultValues?.organization_country || '', organization_city: defaultValues?.organization_city || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, hours_per_week: d.hours_per_week ? Number(d.hours_per_week) : null }))} className="space-y-3">
      <Select label="Type" options={WORK_EXPERIENCE_TYPES} {...register('experience_type')} />
      <Input label="Organization" placeholder="Google, Red Cross..." {...register('organization')} />
      <Input label="Role / Title" placeholder="Software Engineer Intern" {...register('role_title')} />
      <Textarea label="Description" placeholder="Responsibilities and tasks..." {...register('description')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Hours/Week" type="number" {...register('hours_per_week')} />
        <Select label="Compensation" options={[{ value: '', label: 'Select...' }, ...COMPENSATION_TYPES]} {...register('compensation_type')} />
      </div>
      <Textarea label="Key Achievements" placeholder="Impact and results..." {...register('key_achievements')} />
      <Input label="Supervisor (optional)" {...register('supervisor_name')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="City" {...register('organization_city')} />
        <Input label="Country" {...register('organization_country')} />
      </div>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('is_current')} /> Currently active</label>
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function CompetitionForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { competition_name: defaultValues?.competition_name || '', domain: defaultValues?.domain || '', level: defaultValues?.level || 'national', role: defaultValues?.role || '', result_placement: defaultValues?.result_placement || '', year: defaultValues?.year || '', team_size: defaultValues?.team_size || '', description: defaultValues?.description || '', link_proof: defaultValues?.link_proof || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, year: d.year ? Number(d.year) : null, team_size: d.team_size ? Number(d.team_size) : null }))} className="space-y-3">
      <Input label="Competition Name" placeholder="MIT Hacking Medicine, IMO..." {...register('competition_name')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Domain" placeholder="CS, Math, Business..." {...register('domain')} />
        <Select label="Level" options={COMPETITION_LEVELS} {...register('level')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Role" placeholder="Participant, Team Lead..." {...register('role')} />
        <Input label="Result / Placement" placeholder="1st place, Finalist..." {...register('result_placement')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Year" type="number" placeholder="2025" {...register('year')} />
        <Input label="Team Size" type="number" {...register('team_size')} />
      </div>
      <Textarea label="Description (optional)" placeholder="What you built or achieved..." {...register('description')} />
      <Input label="Proof Link (optional)" type="url" placeholder="https://..." {...register('link_proof')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function AccommodationForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { accommodations_needed: defaultValues?.accommodations_needed || false, category: defaultValues?.category || '', details_text: defaultValues?.details_text || '', documentation_status: defaultValues?.documentation_status || 'none', dyslexia_friendly_mode: defaultValues?.dyslexia_friendly_mode || false, font_size_pref: defaultValues?.font_size_pref || 'default' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('accommodations_needed')} /> I need accommodations</label>
      <Select label="Category (optional)" options={[{ value: '', label: 'Select...' }, ...ACCOMMODATION_CATEGORIES]} {...register('category')} />
      <Textarea label="Details (optional)" placeholder="Describe your accommodation needs..." {...register('details_text')} />
      <Select label="Documentation Status" options={DOC_STATUS_OPTIONS} {...register('documentation_status')} />
      <div className="border-t border-stone-100 pt-3 mt-3">
        <p className="text-xs text-stone-500 mb-2">Display preferences</p>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('dyslexia_friendly_mode')} /> Dyslexia-friendly mode</label>
        <Select label="Font Size" options={FONT_SIZE_OPTIONS} {...register('font_size_pref')} />
      </div>
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function SchedulingForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { timezone: defaultValues?.timezone || '', preferred_interview_format: defaultValues?.preferred_interview_format || 'no_preference', campus_visit_interest: defaultValues?.campus_visit_interest || false, notes: defaultValues?.notes || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Timezone" placeholder="America/New_York, Asia/Shanghai..." {...register('timezone')} />
      <Select label="Preferred Interview Format" options={INTERVIEW_FORMAT_OPTIONS} {...register('preferred_interview_format')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('campus_visit_interest')} /> Interested in campus visits</label>
      <Textarea label="Notes (optional)" placeholder="Availability notes, scheduling preferences..." {...register('notes')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

export function VisaInfoForm({ defaultValues, onSubmit, loading }: FormProps) {
  const { register, handleSubmit } = useForm({ defaultValues: { current_immigration_status: defaultValues?.current_immigration_status || '', visa_required: defaultValues?.visa_required || false, target_study_country: defaultValues?.target_study_country || '', passport_expiration_date: defaultValues?.passport_expiration_date?.slice(0, 10) || '', sponsorship_source: defaultValues?.sponsorship_source || '', financial_proof_available: defaultValues?.financial_proof_available || false, financial_proof_amount_band: defaultValues?.financial_proof_amount_band || '', post_study_work_interest: defaultValues?.post_study_work_interest || false, prior_visa_refusals: defaultValues?.prior_visa_refusals || false, travel_constraints: defaultValues?.travel_constraints || '', work_authorization_needed: defaultValues?.work_authorization_needed || false } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Current Immigration Status" placeholder="F-1, H-1B, citizen..." {...register('current_immigration_status')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('visa_required')} /> Visa required for target country</label>
      <Input label="Target Study Country" placeholder="United States, Canada..." {...register('target_study_country')} />
      <Input label="Passport Expiration" type="date" {...register('passport_expiration_date')} />
      <Select label="Sponsorship Source" options={[{ value: '', label: 'Select...' }, ...SPONSORSHIP_SOURCES]} {...register('sponsorship_source')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('financial_proof_available')} /> Financial proof available</label>
      <Input label="Financial Proof Amount Band" placeholder="$20k-$50k..." {...register('financial_proof_amount_band')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('post_study_work_interest')} /> Interested in post-study work (OPT/PGWP)</label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('prior_visa_refusals')} /> Prior visa refusals</label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('work_authorization_needed')} /> Need work authorization during study</label>
      <Textarea label="Travel Constraints (optional)" placeholder="Any travel restrictions..." {...register('travel_constraints')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}
