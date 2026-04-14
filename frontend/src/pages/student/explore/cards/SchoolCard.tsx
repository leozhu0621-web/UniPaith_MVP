import { useNavigate } from 'react-router-dom'
import { GraduationCap, MapPin, BookOpen, Users, TrendingUp } from 'lucide-react'

interface SchoolData {
  id: string
  name: string
  country: string
  city?: string | null
  type?: string | null
  campus_setting?: string | null
  student_body_size?: number | null
  logo_url?: string | null
  image_url?: string | null
  program_count?: number
  description_text?: string | null
  acceptance_rate?: number | null
  sat_avg?: number | null
  us_news_rank?: number | null
  median_earnings?: number | null
  graduation_rate?: number | null
}

interface Props {
  institution: SchoolData
}

export default function SchoolCard({ institution: inst }: Props) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/s/institutions/${inst.id}`)}
      className="bg-white rounded-xl border border-divider hover:shadow-lg transition-all overflow-hidden cursor-pointer flex flex-col"
    >
      {/* Image */}
      <div className="relative h-32 bg-student-mist overflow-hidden">
        {inst.image_url ? (
          <img src={inst.image_url} alt={inst.name} className="w-full h-full object-cover" onError={e => (e.currentTarget.style.display = 'none')} />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <GraduationCap size={32} className="text-student/20" />
          </div>
        )}
        {inst.logo_url && (
          <div className="absolute bottom-2 left-2 w-10 h-10 rounded-lg bg-white shadow-sm border border-divider p-1">
            <img src={inst.logo_url} alt="" className="w-full h-full object-contain" onError={e => (e.currentTarget.style.display = 'none')} />
          </div>
        )}
        {inst.us_news_rank && (
          <span className="absolute top-2 right-2 px-2 py-0.5 text-[10px] font-bold rounded-full bg-gold-soft text-gold border border-gold/20">
            #{inst.us_news_rank}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 px-4 pt-3 pb-2">
        <h3 className="text-sm font-bold text-student-ink leading-tight mb-1">{inst.name}</h3>
        <div className="flex items-center gap-1.5 text-xs text-student-text mb-2">
          <MapPin size={10} />
          <span>{inst.city ? `${inst.city}, ` : ''}{inst.country}</span>
          {inst.type && <><span className="text-student-text/40">·</span><span className="capitalize">{inst.type}</span></>}
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-student-text mb-2">
          {inst.program_count != null && inst.program_count > 0 && (
            <span className="flex items-center gap-0.5"><BookOpen size={9} /> {inst.program_count} programs</span>
          )}
          {inst.student_body_size != null && (
            <span className="flex items-center gap-0.5"><Users size={9} /> {inst.student_body_size.toLocaleString()}</span>
          )}
          {inst.acceptance_rate != null && (
            <span className="flex items-center gap-0.5"><GraduationCap size={9} /> {Math.round(inst.acceptance_rate * 100)}%</span>
          )}
          {inst.median_earnings != null && (
            <span className="flex items-center gap-0.5"><TrendingUp size={9} /> ${Math.round(inst.median_earnings / 1000)}K</span>
          )}
          {inst.sat_avg != null && <span>SAT {inst.sat_avg}</span>}
        </div>
        {inst.description_text && (
          <p className="text-[10px] text-student-text line-clamp-2 leading-relaxed">{inst.description_text}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center border-t border-divider mt-auto">
        <button className="flex-1 py-2 text-[11px] font-medium text-student hover:bg-student-mist transition-colors text-center">
          View Programs
        </button>
        <div className="w-px h-5 bg-divider" />
        <button className="flex-1 py-2 text-[11px] font-medium text-student-text hover:bg-student-mist hover:text-student-ink transition-colors text-center">
          School Profile
        </button>
      </div>
    </div>
  )
}
