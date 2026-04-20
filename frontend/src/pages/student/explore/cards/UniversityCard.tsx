import { useState } from 'react'
import {
  MapPin, Users, Building2, BookOpen, ChevronRight,
  Sprout, Landmark,
} from 'lucide-react'
import { classifyInstitution, sizeBucket, formatSetting, SIZE_OPTIONS } from '../shared/classifyInstitution'

interface UniversityData {
  id: string
  name: string
  country: string
  city?: string | null
  region?: string | null
  type?: string | null
  campus_setting?: string | null
  student_body_size?: number | null
  logo_url?: string | null
  image_url?: string | null
  program_count?: number
  school_count?: number
  description_text?: string | null
  subjects_offered?: string[] | null
  top_industries?: string[] | null
  // Competitive fields (no longer shown on the card — live on the detail page):
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

  // Trust only what the DB gives us. A missing image still reads as a
  // proper card because the university name is the visual anchor.
  const campusImg = inst.image_url
  const logoImg = inst.logo_url

  const classification = classifyInstitution({
    description_text: inst.description_text,
    type: inst.type,
  })
  const settingLabel = formatSetting(inst.campus_setting)
  const size = sizeBucket(inst.student_body_size)
  const sizeLabel = size ? SIZE_OPTIONS.find(s => s.code === size)?.label ?? null : null

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-divider hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden cursor-pointer flex flex-col group/card"
    >
      {/* ── Image with strong name watermark ── */}
      <div className="relative h-44 bg-student-mist overflow-hidden">
        {campusImg && !imgFailed ? (
          <img
            src={campusImg}
            alt={inst.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover/card:scale-[1.03]"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-student via-student/80 to-student-hover" />
        )}

        {/* Strong scrim — keeps the name legible over any photo */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/45 to-black/15 pointer-events-none" />

        {/* Logo chip — top-left, doesn't compete with the name */}
        {logoImg && (
          <div className="absolute top-3 left-3 w-9 h-9 rounded-lg bg-white/95 shadow-sm border border-white/50 p-1 flex items-center justify-center">
            <img
              src={logoImg}
              alt=""
              className="w-full h-full object-contain"
              onError={e => (e.currentTarget.parentElement!.style.display = 'none')}
            />
          </div>
        )}

        {/* Name as the visual anchor — large, centered-left, drop shadow */}
        <div className="absolute inset-0 flex flex-col justify-end px-4 pb-4 pointer-events-none">
          <h3
            className="text-white text-[22px] leading-[1.1] font-bold drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)] tracking-tight line-clamp-2"
            style={{ fontFamily: 'var(--font-display, inherit)' }}
          >
            {inst.name}
          </h3>
          <div className="flex items-center gap-1.5 mt-1.5 text-white/90 text-[11px] drop-shadow-sm">
            <MapPin size={10} className="flex-shrink-0" />
            <span className="truncate">
              {inst.city ? `${inst.city}, ` : ''}{inst.region ? `${inst.region} · ` : ''}{inst.country}
            </span>
          </div>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex-1 px-4 pt-3 pb-3 flex flex-col">
        {/* Welcoming-pill row: Type · Setting · Size · schools · programs */}
        <div className="flex flex-wrap items-center gap-1.5 mb-3">
          {classification.code !== 'other' && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-md bg-student-mist text-student border border-student/15">
              <Landmark size={10} />
              {classification.label}
            </span>
          )}
          {settingLabel && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
              <Sprout size={10} className="text-slate-400" />
              {settingLabel}
            </span>
          )}
          {sizeLabel && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
              <Users size={10} className="text-slate-400" />
              {sizeLabel}
            </span>
          )}
          {(inst.school_count ?? 0) > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
              <Building2 size={10} className="text-slate-400" />
              {inst.school_count} schools
            </span>
          )}
          {(inst.program_count ?? 0) > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
              <BookOpen size={10} className="text-slate-400" />
              {inst.program_count} programs
            </span>
          )}
        </div>

        {/* Description — 2 lines max, pushes footer to the bottom */}
        {inst.description_text && (
          <p className="text-[11.5px] text-student-text/80 leading-relaxed line-clamp-2 mb-3 flex-1">
            {inst.description_text}
          </p>
        )}
      </div>

      {/* ── Footer action ── */}
      <div className="flex items-center border-t border-divider mt-auto px-4 py-2.5">
        <span className="text-xs font-medium text-student flex-1">View University</span>
        <ChevronRight size={16} className="text-student group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}
