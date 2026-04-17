import {
  Target, TrendingUp, DollarSign, Building2,
  Award, Percent, GraduationCap, Calendar,
  Wallet, Landmark, CreditCard, Users,
} from 'lucide-react'
import { formatCurrency, formatPercent, formatDate } from '../../../utils/format'

interface Props {
  // Admissions
  acceptanceRate?: number | null
  satAvg?: number | null
  actMidpoint?: number | null
  applicationDeadline?: string | null

  // Outcomes
  earnings6yr?: number | null
  earnings10yr?: number | null
  graduationRate?: number | null
  retentionRate?: number | null
  employmentRate?: number | null

  // Costs
  tuition?: number | null
  totalCost?: number | null
  netPrice?: number | null
  medianDebt?: number | null
  pellGrantRate?: number | null

  // Scale
  studentBodySize?: number | null
  campusSetting?: string | null
  institutionType?: string | null
}

type StatItem = {
  icon: any
  label: string
  value: string
  tone?: 'emerald' | 'blue' | 'amber' | 'rose'
}

function StatCard({ icon: Icon, label, value, tone }: StatItem) {
  const toneClass = {
    emerald: 'text-emerald-700',
    blue: 'text-blue-700',
    amber: 'text-amber-700',
    rose: 'text-rose-700',
  }[tone || '']

  return (
    <div className="flex items-center gap-2.5 px-3 py-2.5 bg-white border border-divider rounded-lg hover:border-student/30 transition-colors">
      <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center flex-shrink-0">
        <Icon size={14} className={toneClass || 'text-student-text'} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-student-text/70 leading-tight uppercase tracking-wide">{label}</p>
        <p className="text-sm font-bold text-student-ink leading-tight truncate">{value}</p>
      </div>
    </div>
  )
}

/** Grid columns that adapt to the number of stats so we never leave awkward empty gaps. */
const GRID_BY_COUNT: Record<number, string> = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-2 md:grid-cols-3',
  4: 'grid-cols-2 md:grid-cols-4',
  5: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5',
  6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
}

function Category({ title, icon: Icon, stats }: { title: string; icon: any; stats: StatItem[] }) {
  if (stats.length === 0) return null
  const gridClass = GRID_BY_COUNT[Math.min(stats.length, 6)] || GRID_BY_COUNT[5]
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-center gap-1.5 mb-2">
        <Icon size={12} className="text-student-text/70" />
        <h4 className="text-[10px] font-semibold text-student-text/70 uppercase tracking-wider">{title}</h4>
      </div>
      <div className={`grid gap-2 ${gridClass}`}>
        {stats.map((s, i) => <StatCard key={i} {...s} />)}
      </div>
    </div>
  )
}

export default function StatGroup(props: Props) {
  const admissions: StatItem[] = []
  if (props.acceptanceRate != null) {
    admissions.push({ icon: Percent, label: 'Acceptance', value: formatPercent(props.acceptanceRate, 1), tone: 'amber' })
  }
  if (props.satAvg) {
    admissions.push({ icon: Award, label: 'SAT Avg', value: String(props.satAvg), tone: 'blue' })
  }
  if (props.actMidpoint) {
    admissions.push({ icon: Award, label: 'ACT Mid', value: String(props.actMidpoint), tone: 'blue' })
  }
  if (props.applicationDeadline) {
    admissions.push({ icon: Calendar, label: 'Deadline', value: formatDate(props.applicationDeadline), tone: 'amber' })
  }

  const outcomes: StatItem[] = []
  if (props.earnings6yr) {
    outcomes.push({ icon: TrendingUp, label: 'Early Salary (6yr)', value: formatCurrency(props.earnings6yr), tone: 'emerald' })
  }
  if (props.earnings10yr) {
    outcomes.push({ icon: TrendingUp, label: 'Mid Salary (10yr)', value: formatCurrency(props.earnings10yr), tone: 'emerald' })
  }
  if (props.graduationRate != null) {
    outcomes.push({ icon: GraduationCap, label: 'Grad Rate', value: `${Math.round(props.graduationRate * 100)}%`, tone: 'emerald' })
  }
  if (props.retentionRate != null) {
    outcomes.push({ icon: Target, label: 'Retention', value: `${Math.round(props.retentionRate * 100)}%`, tone: 'blue' })
  }
  if (props.employmentRate != null) {
    outcomes.push({ icon: Target, label: 'Employment', value: `${Math.round(props.employmentRate * 100)}%`, tone: 'emerald' })
  }

  const costs: StatItem[] = []
  if (props.tuition != null) {
    costs.push({ icon: DollarSign, label: 'Tuition/yr', value: formatCurrency(props.tuition), tone: 'rose' })
  }
  if (props.totalCost) {
    costs.push({ icon: Wallet, label: 'Total Cost/yr', value: formatCurrency(props.totalCost), tone: 'rose' })
  }
  if (props.netPrice) {
    costs.push({ icon: CreditCard, label: 'Avg Net Price', value: formatCurrency(props.netPrice), tone: 'blue' })
  }
  if (props.medianDebt) {
    costs.push({ icon: Landmark, label: 'Median Debt', value: formatCurrency(props.medianDebt), tone: 'amber' })
  }
  if (props.pellGrantRate != null) {
    costs.push({ icon: Percent, label: 'Pell Grant', value: `${Math.round(props.pellGrantRate * 100)}%`, tone: 'blue' })
  }

  const scale: StatItem[] = []
  if (props.studentBodySize) {
    scale.push({ icon: Users, label: 'Student Body', value: props.studentBodySize.toLocaleString() })
  }
  if (props.campusSetting) {
    scale.push({ icon: Building2, label: 'Setting', value: props.campusSetting })
  }
  if (props.institutionType) {
    scale.push({ icon: Building2, label: 'Type', value: props.institutionType })
  }

  return (
    <div className="mb-6">
      <Category title="Admissions" icon={Target} stats={admissions} />
      <Category title="Outcomes" icon={TrendingUp} stats={outcomes} />
      <Category title="Costs & Aid" icon={DollarSign} stats={costs} />
      <Category title="Scale" icon={Building2} stats={scale} />
    </div>
  )
}
