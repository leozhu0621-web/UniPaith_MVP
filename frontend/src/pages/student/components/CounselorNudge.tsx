import { useNavigate } from 'react-router-dom'
import { Sparkles, PartyPopper, AlertTriangle, ArrowRight, MessageSquare } from 'lucide-react'

interface CounselorNudgeProps {
  message: string
  actionLabel: string
  actionTo: string
  variant?: 'suggestion' | 'celebrate' | 'urgent'
  counselorLink?: string // optional "Ask counselor" link
}

const VARIANT_STYLES = {
  suggestion: {
    bg: 'bg-blue-50 border-blue-100',
    icon: Sparkles,
    iconColor: 'text-blue-500',
    textColor: 'text-blue-800',
    btnBg: 'bg-blue-600 hover:bg-blue-700 text-white',
  },
  celebrate: {
    bg: 'bg-emerald-50 border-emerald-100',
    icon: PartyPopper,
    iconColor: 'text-emerald-500',
    textColor: 'text-emerald-800',
    btnBg: 'bg-emerald-600 hover:bg-emerald-700 text-white',
  },
  urgent: {
    bg: 'bg-amber-50 border-amber-100',
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
    textColor: 'text-amber-800',
    btnBg: 'bg-amber-600 hover:bg-amber-700 text-white',
  },
}

export default function CounselorNudge({
  message,
  actionLabel,
  actionTo,
  variant = 'suggestion',
  counselorLink,
}: CounselorNudgeProps) {
  const navigate = useNavigate()
  const style = VARIANT_STYLES[variant]
  const Icon = style.icon

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${style.bg}`}>
      <Icon size={18} className={`flex-shrink-0 ${style.iconColor}`} />
      <p className={`flex-1 text-sm ${style.textColor}`}>{message}</p>
      <div className="flex items-center gap-2 flex-shrink-0">
        {counselorLink && (
          <button
            onClick={() => navigate(counselorLink)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
          >
            <MessageSquare size={12} /> Ask counselor
          </button>
        )}
        <button
          onClick={() => navigate(actionTo)}
          className={`flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${style.btnBg}`}
        >
          {actionLabel} <ArrowRight size={12} />
        </button>
      </div>
    </div>
  )
}
