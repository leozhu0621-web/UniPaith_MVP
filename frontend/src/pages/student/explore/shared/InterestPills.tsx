import {
  Sparkles, Monitor, Briefcase, Wrench, Heart, Palette, BookOpen, Scale,
} from 'lucide-react'

const PILLS = [
  { key: 'all', label: 'For You', icon: Sparkles },
  { key: 'Computer Science', label: 'CS & Tech', icon: Monitor },
  { key: 'Business', label: 'Business', icon: Briefcase },
  { key: 'Engineering', label: 'Engineering', icon: Wrench },
  { key: 'Health', label: 'Health', icon: Heart },
  { key: 'Arts', label: 'Arts & Design', icon: Palette },
  { key: 'Education', label: 'Education', icon: BookOpen },
  { key: 'Law', label: 'Law', icon: Scale },
]

interface Props {
  active: string
  onChange: (key: string) => void
}

export default function InterestPills({ active, onChange }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      {PILLS.map(p => (
        <button
          key={p.key}
          onClick={() => onChange(p.key)}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
            active === p.key
              ? 'bg-student text-white'
              : 'bg-white border border-stone text-student-text hover:border-student hover:text-student-ink'
          }`}
        >
          <p.icon size={12} />
          {p.label}
        </button>
      ))}
    </div>
  )
}

export { PILLS as INTEREST_PILLS }
