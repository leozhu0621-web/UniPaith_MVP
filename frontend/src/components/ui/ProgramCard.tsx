// ProgramCard — canonical display-card schema for programs.
// Spec/02-design-system.md §5 "Display card pattern" — single schema
// reused across Discovery, Compare, Saved, Detail headers, and
// institution program directories. Hover/focus surfaces three actions:
// Save · Add to Compare · Open.
//
// Standard phrasings per Spec §16: "Save to my list", "Add to compare".

import { useState } from 'react'
import clsx from 'clsx'
import { Bookmark, GitCompare, ArrowRight, MapPin, Clock, GraduationCap, Wifi } from 'lucide-react'
import Card from './Card'
import { BandBadge, ConfidenceDots, type Band } from './Badge'

export type ProgramCardData = {
  id: string
  name: string
  schoolName: string
  schoolId: string
  location: { city: string; region: string; country: string }
  degreeType:
    | 'certificate'
    | 'associate'
    | 'bachelor'
    | 'master'
    | 'doctorate'
    | 'professional'
  deliveryFormat: 'in_person' | 'online' | 'hybrid'
  durationMonths?: number | null
  costSignal?: { tuitionBand: string; currency: string } | null
  selectivitySignal?: 'open' | 'moderate' | 'selective' | 'highly_selective' | null
  outcomesHighlights?: string[]
  // Match-context (only when rendered inside a match/saved context).
  fitnessScore?: number
  confidenceScore?: number
  bandLabel?: Band
}

interface ProgramCardProps {
  program: ProgramCardData
  onOpen?: (id: string) => void
  onSave?: (id: string) => void
  onCompare?: (id: string) => void
  saved?: boolean
  inCompare?: boolean
  /** Override default card padding (16/24px). */
  compact?: boolean
  className?: string
}

const DEGREE_LABEL: Record<ProgramCardData['degreeType'], string> = {
  certificate: 'Certificate',
  associate: 'Associate',
  bachelor: "Bachelor's",
  master: "Master's",
  doctorate: 'Doctorate',
  professional: 'Professional',
}

const DELIVERY_LABEL: Record<ProgramCardData['deliveryFormat'], string> = {
  in_person: 'In person',
  online: 'Online',
  hybrid: 'Hybrid',
}

export default function ProgramCard({
  program,
  onOpen,
  onSave,
  onCompare,
  saved,
  inCompare,
  compact,
  className,
}: ProgramCardProps) {
  const [hovered, setHovered] = useState(false)
  const locationLine = [program.location.city, program.location.region].filter(Boolean).join(', ')
  const confDots = program.confidenceScore != null ? Math.round((program.confidenceScore / 100) * 5) : null

  return (
    <Card
      variant="card"
      padding="none"
      className={clsx('group', className)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
    >
      <div className={clsx(compact ? 'p-4' : 'p-6', 'flex flex-col gap-3 h-full')}>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="up-eyebrow mb-1 truncate" title={program.schoolName}>
              {program.schoolName}
            </div>
            <h3 className="text-[18px] leading-[1.25] font-bold text-foreground line-clamp-2">
              {program.name}
            </h3>
          </div>
          {program.bandLabel && <BandBadge band={program.bandLabel} />}
        </div>

        <div className="flex flex-wrap gap-x-3 gap-y-1.5 text-[13px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <GraduationCap size={14} aria-hidden /> {DEGREE_LABEL[program.degreeType]}
          </span>
          <span className="inline-flex items-center gap-1">
            <Wifi size={14} aria-hidden /> {DELIVERY_LABEL[program.deliveryFormat]}
          </span>
          {locationLine && (
            <span className="inline-flex items-center gap-1 truncate" title={locationLine}>
              <MapPin size={14} aria-hidden /> {locationLine}
            </span>
          )}
          {program.durationMonths != null && (
            <span className="inline-flex items-center gap-1">
              <Clock size={14} aria-hidden /> {program.durationMonths} mo
            </span>
          )}
        </div>

        {program.outcomesHighlights && program.outcomesHighlights.length > 0 && (
          <ul className="text-[13px] text-foreground/80 space-y-0.5">
            {program.outcomesHighlights.slice(0, 3).map(h => (
              <li key={h} className="truncate">— {h}</li>
            ))}
          </ul>
        )}

        <div className="mt-auto pt-3 border-t border-border flex items-center justify-between gap-2">
          {program.fitnessScore != null ? (
            <div className="flex flex-col gap-0.5">
              <span className="up-eyebrow text-muted-foreground" style={{ color: 'inherit' }}>
                Fitness
              </span>
              <span className="text-[20px] font-bold tabular-nums leading-none">
                {Math.round(program.fitnessScore)}
              </span>
            </div>
          ) : (
            <div className="text-[13px] text-muted-foreground">
              {program.costSignal?.tuitionBand}
            </div>
          )}
          {confDots != null && <ConfidenceDots filled={confDots} showLabel />}
        </div>

        <div
          className={clsx(
            'flex items-center gap-1.5 transition-opacity motion-base',
            hovered ? 'opacity-100' : 'opacity-0 group-focus-within:opacity-100',
          )}
        >
          {onSave && (
            <button
              type="button"
              onClick={() => onSave(program.id)}
              aria-label={saved ? 'Remove from list' : 'Save to my list'}
              className={clsx(
                'inline-flex items-center justify-center h-9 px-2 rounded-md text-[13px] font-bold motion-fast transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
                saved
                  ? 'bg-[#FFD60A] text-[#2A2724] dark:bg-[#F2C800] dark:text-[#0A1428]'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              <Bookmark size={16} aria-hidden />
              <span className="ml-1.5">{saved ? 'Saved' : 'Save'}</span>
            </button>
          )}
          {onCompare && (
            <button
              type="button"
              onClick={() => onCompare(program.id)}
              aria-label={inCompare ? 'Remove from compare' : 'Add to compare'}
              className={clsx(
                'inline-flex items-center justify-center h-9 px-2 rounded-md text-[13px] font-bold motion-fast transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
                inCompare
                  ? 'bg-[#2A6BD4] text-[#FCFAF2] dark:bg-[#6FA0E8] dark:text-[#0A1428]'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              <GitCompare size={16} aria-hidden />
              <span className="ml-1.5">Compare</span>
            </button>
          )}
          {onOpen && (
            <button
              type="button"
              onClick={() => onOpen(program.id)}
              aria-label={`Open ${program.name}`}
              className="ml-auto inline-flex items-center justify-center h-9 px-3 rounded-md bg-[#2A6BD4] text-[#FCFAF2] text-[13px] font-bold hover:bg-[#1F58B5] dark:bg-[#6FA0E8] dark:text-[#0A1428] dark:hover:bg-[#9CC0F0] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
            >
              Open <ArrowRight size={14} className="ml-1" />
            </button>
          )}
        </div>
      </div>
    </Card>
  )
}
