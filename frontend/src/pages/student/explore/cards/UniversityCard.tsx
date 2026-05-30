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
      {/* ── Header — campus photo when present, else an editorial ink panel.
           No gold/technicolor gradient fill (Spec/01 §1 — "yellow is
           punctuation, not fill"; "restraint over decoration"). ── */}
      <div className="relative h-44 bg-ink-deep overflow-hidden">
        {campusImg && !imgFailed ? (
          <>
            <img
              src={campusImg}
              alt={inst.name}
              className="w-full h-full object-cover transition-transform duration-300 group-hover/card:scale-[1.03]"
              onError={() => setImgFailed(true)}
            />
            {/* Ink scrim — functional legibility for the name over a photo */}
            <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-ink-deep via-ink-deep/55 to-transparent pointer-events-none" />
          </>
        ) : (
          /* Editorial ink panel — a faint gold landmark is the only accent */
          <div className="absolute inset-0 flex items-center justify-center">
            <Landmark size={64} strokeWidth={1.5} className="text-gold/15" />
          </div>
        )}

        {/* Logo chip — top-left, doesn't compete with the name */}
        {logoImg && (
          <div className="absolute top-3 left-3 w-9 h-9 rounded-md bg-white/95 shadow-sm border border-white/50 p-1 flex items-center justify-center">
            <img
              src={logoImg}
              alt=""
              className="w-full h-full object-contain"
              onError={e => (e.currentTarget.parentElement!.style.display = 'none')}
            />
          </div>
        )}

        {/* Name anchor — cream-on-ink, editorial */}
        <div className="absolute inset-0 flex flex-col justify-end px-4 pb-4 pointer-events-none">
          <h3 className="text-white text-[22px] leading-[1.1] font-bold tracking-tight line-clamp-2">
            {inst.name}
          </h3>
          <div className="flex items-center gap-1.5 mt-1.5 text-cream/85 text-[11px]">
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
