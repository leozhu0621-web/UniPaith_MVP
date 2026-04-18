import {
  GraduationCap, Building2, MapPin, Clock, Calendar,
  FileCheck, Globe, Users as UsersIcon,
} from 'lucide-react'
import { DEGREE_LABELS } from '../../../utils/constants'
import { formatDate } from '../../../utils/format'

interface Props {
  degreeType: string
  deliveryFormat?: string | null
  campusSetting?: string | null
  durationMonths?: number | null
  applicationDeadline?: string | null
  programStartDate?: string | null
  testPolicy?: string | null
  languageOfInstruction?: string | null
  studentBodySize?: number | null
}

function pillStyle(variant: 'academic' | 'logistics' | 'time' | 'deadline') {
  switch (variant) {
    case 'academic':
      return 'bg-student-mist text-student border border-student/15'
    case 'logistics':
      return 'bg-slate-100 text-student-ink border border-slate-200/60'
    case 'time':
      return 'bg-slate-100 text-student-ink border border-slate-200/60'
    case 'deadline':
      return 'bg-amber-50 text-amber-700 border border-amber-200'
  }
}

function durationLabel(months?: number | null, degreeType?: string): string | null {
  if (months) {
    if (months >= 12) {
      const y = Math.round(months / 12)
      return `${y} year${y > 1 ? 's' : ''}`
    }
    return `${months} months`
  }
  if (degreeType === 'bachelors') return '4 years'
  if (degreeType === 'masters') return '1–2 years'
  if (degreeType === 'phd') return '4–6 years'
  return null
}

export default function InfoPillRow({
  degreeType,
  deliveryFormat,
  campusSetting,
  durationMonths,
  applicationDeadline,
  programStartDate,
  testPolicy,
  languageOfInstruction,
  studentBodySize,
}: Props) {
  const duration = durationLabel(durationMonths, degreeType)

  const pills: Array<{ icon: any; label: string; variant: Parameters<typeof pillStyle>[0]; hint?: string }> = []

  pills.push({
    icon: GraduationCap,
    label: DEGREE_LABELS[degreeType] || degreeType,
    variant: 'academic',
  })

  if (deliveryFormat) {
    pills.push({
      icon: Building2,
      label: deliveryFormat.replace(/_/g, ' '),
      variant: 'logistics',
    })
  }

  if (campusSetting) {
    pills.push({
      icon: MapPin,
      label: campusSetting,
      variant: 'logistics',
    })
  }

  if (duration) {
    pills.push({
      icon: Clock,
      label: duration,
      variant: 'time',
    })
  }

  if (languageOfInstruction) {
    pills.push({
      icon: Globe,
      label: languageOfInstruction,
      variant: 'logistics',
    })
  }

  if (testPolicy) {
    pills.push({
      icon: FileCheck,
      label: testPolicy,
      variant: 'logistics',
    })
  }

  if (studentBodySize && studentBodySize > 0) {
    pills.push({
      icon: UsersIcon,
      label: `${studentBodySize.toLocaleString()} students`,
      variant: 'logistics',
    })
  }

  if (programStartDate) {
    pills.push({
      icon: Calendar,
      label: `Starts ${formatDate(programStartDate)}`,
      variant: 'time',
    })
  }

  if (applicationDeadline) {
    pills.push({
      icon: Calendar,
      label: `Deadline: ${formatDate(applicationDeadline)}`,
      variant: 'deadline',
    })
  }

  return (
    <div className="flex flex-wrap gap-2 mb-5">
      {pills.map((pill, i) => (
        <span
          key={i}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full capitalize ${pillStyle(pill.variant)}`}
          title={pill.hint}
        >
          <pill.icon size={12} className="flex-shrink-0" />
          {pill.label}
        </span>
      ))}
    </div>
  )
}
