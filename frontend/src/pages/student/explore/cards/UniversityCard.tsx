import { useState } from 'react'
import {
  GraduationCap, MapPin, Users, TrendingUp,
  Award, Building2, BookOpen, ChevronRight,
} from 'lucide-react'

// Local school images
const LOCAL_IMAGES: Record<string, { campus: string[]; logo?: string }> = {
  'new york university': {
    campus: ['/school-images/nyu-campus-1.jpg', '/school-images/nyu-campus-2.jpg', '/school-images/nyu-campus-3.jpg'],
    logo: '/school-images/nyu-logo.jpg',
  },
  'stanford university': {
    campus: ['/school-images/stanford-campus.jpg'],
    logo: '/school-images/stanford-logo.jpg',
  },
}

interface UniversityData {
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
  school_count?: number
  description_text?: string | null
  acceptance_rate?: number | null
  sat_avg?: number | null
  us_news_rank?: number | null
  median_earnings?: number | null
  graduation_rate?: number | null
}

interface Props {
  institution: UniversityData
  onClick: () => void
}

export default function UniversityCard({ institution: inst, onClick }: Props) {
  const [imgFailed, setImgFailed] = useState(false)
  const local = LOCAL_IMAGES[(inst.name || '').toLowerCase()]
  const campusImg = local?.campus[0] || inst.image_url
  const logoImg = local?.logo || inst.logo_url

  const acceptPct = inst.acceptance_rate != null ? Math.round(inst.acceptance_rate * 100) : null

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-divider hover:shadow-lg hover:scale-[1.005] hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden cursor-pointer flex flex-col group/card"
    >
      {/* ── Image ── */}
      <div className="relative h-44 bg-student-mist overflow-hidden">
        {campusImg && !imgFailed ? (
          <img
            src={campusImg}
            alt={inst.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover/card:scale-105"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-student-mist to-student/5">
            <Building2 size={40} className="text-student/15" />
          </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/5 to-transparent pointer-events-none" />

        {/* Ranking */}
        {inst.us_news_rank && (
          <div className="absolute top-3 right-3 flex items-center gap-1 px-2.5 py-1 rounded-full bg-gold-soft/90 text-gold border border-gold/20 shadow-sm backdrop-blur-sm">
            <Award size={10} />
            <span className="text-[10px] font-bold">#{inst.us_news_rank}</span>
          </div>
        )}

        {/* Bottom: logo + name */}
        <div className="absolute bottom-3 left-3 right-3 flex items-end gap-2.5">
          {logoImg && (
            <div className="w-12 h-12 rounded-xl bg-white shadow-md border border-white/50 p-1.5 flex-shrink-0">
              <img src={logoImg} alt="" className="w-full h-full object-contain" onError={e => (e.currentTarget.parentElement!.style.display = 'none')} />
            </div>
          )}
          <div className="min-w-0">
            <h3 className="text-white text-base font-bold truncate drop-shadow-sm">{inst.name}</h3>
            <div className="flex items-center gap-1.5 text-white/80 text-[11px]">
              <MapPin size={9} className="flex-shrink-0" />
              <span className="truncate">{inst.city ? `${inst.city}, ` : ''}{inst.country}</span>
              {inst.type && (
                <>
                  <span className="text-white/40">·</span>
                  <span className="capitalize">{inst.type}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      <div className="flex-1 px-4 pt-3 pb-3">
        {/* School & program counts */}
        <div className="flex items-center gap-3 text-xs text-student-text mb-2">
          {(inst.school_count ?? 0) > 0 && (
            <span className="flex items-center gap-1">
              <Building2 size={11} className="text-student" />
              <span className="font-semibold text-student-ink">{inst.school_count}</span> schools
            </span>
          )}
          {(inst.program_count ?? 0) > 0 && (
            <span className="flex items-center gap-1">
              <BookOpen size={11} className="text-student" />
              <span className="font-semibold text-student-ink">{inst.program_count}</span> programs
            </span>
          )}
        </div>

        {/* Description */}
        {inst.description_text && (
          <p className="text-[11px] text-student-text/80 leading-relaxed line-clamp-2 mb-3">
            {inst.description_text}
          </p>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-1.5">
          {acceptPct != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <GraduationCap size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Acceptance</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{acceptPct}%</p>
              </div>
            </div>
          )}
          {inst.median_earnings != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <TrendingUp size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Avg Salary</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">${Math.round(inst.median_earnings / 1000)}K</p>
              </div>
            </div>
          )}
          {inst.student_body_size != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <Users size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Students</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{inst.student_body_size.toLocaleString()}</p>
              </div>
            </div>
          )}
          {inst.sat_avg != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <Award size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">SAT Avg</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{inst.sat_avg}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Action ── */}
      <div className="flex items-center border-t border-divider mt-auto px-4 py-2.5">
        <span className="text-xs font-medium text-student flex-1">Explore Schools</span>
        <ChevronRight size={16} className="text-student group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}
