import { useForm } from 'react-hook-form'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Textarea from '../../../components/ui/Textarea'
import Select from '../../../components/ui/Select'
import { DEGREE_LABELS, TEST_TYPES, ACTIVITY_TYPES, GPA_SCALES, CITY_SIZE_OPTIONS, FUNDING_OPTIONS } from '../../../utils/constants'

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
