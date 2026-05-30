// SchoolCard — canonical display-card schema for institutions.
// Spec/02-design-system.md §5.

import { useState } from 'react'
import clsx from 'clsx'
import { Bookmark, ArrowRight, MapPin, Building2, Users } from 'lucide-react'
import Card from './Card'

export type SchoolCardData = {
  id: string
  name: string
  location: { city: string; region: string; country: string }
  campusSetting?: 'urban' | 'suburban' | 'rural'
  size?: 'small' | 'medium' | 'large' | 'very_large' | null
  type?: 'public' | 'private' | 'community' | 'vocational' | 'for_profit'
  highlights?: string[]
}

interface SchoolCardProps {
  school: SchoolCardData
  onOpen?: (id: string) => void
  onSave?: (id: string) => void
  onCompare?: (id: string) => void
  saved?: boolean
  inCompare?: boolean
  className?: string
}

const TYPE_LABEL: Record<NonNullable<SchoolCardData['type']>, string> = {
  public: 'Public',
  private: 'Private',
  community: 'Community',
  vocational: 'Vocational',
  for_profit: 'For-profit',
}

const SIZE_LABEL: Record<NonNullable<SchoolCardData['size']>, string> = {
  small: 'Small',
  medium: 'Medium',
  large: 'Large',
  very_large: 'Very large',
}

const SETTING_LABEL: Record<NonNullable<SchoolCardData['campusSetting']>, string> = {
  urban: 'Urban',
  suburban: 'Suburban',
  rural: 'Rural',
}

export default function SchoolCard({
  school,
  onOpen,
  onSave,
  onCompare,
  saved,
  inCompare,
  className,
}: SchoolCardProps) {
  const [hovered, setHovered] = useState(false)
  const locationLine = [school.location.city, school.location.region, school.location.country]
    .filter(Boolean)
    .join(', ')

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
      <div className="p-6 flex flex-col gap-3 h-full">
        <div className="min-w-0 flex-1">
          <div className="up-eyebrow mb-1">Institution</div>
          <h3 className="text-[20px] leading-[1.3] font-bold text-foreground line-clamp-2">
            {school.name}
          </h3>
        </div>

        <div className="flex flex-wrap gap-x-3 gap-y-1.5 text-[13px] text-muted-foreground">
          {locationLine && (
            <span className="inline-flex items-center gap-1 truncate" title={locationLine}>
              <MapPin size={14} aria-hidden /> {locationLine}
            </span>
          )}
          {school.type && (
            <span className="inline-flex items-center gap-1">
              <Building2 size={14} aria-hidden /> {TYPE_LABEL[school.type]}
            </span>
          )}
          {school.size && (
            <span className="inline-flex items-center gap-1">
              <Users size={14} aria-hidden /> {SIZE_LABEL[school.size]}
            </span>
          )}
          {school.campusSetting && (
            <span>{SETTING_LABEL[school.campusSetting]}</span>
          )}
        </div>

        {school.highlights && school.highlights.length > 0 && (
          <ul className="text-[13px] text-foreground/80 space-y-0.5">
            {school.highlights.slice(0, 3).map(h => (
              <li key={h} className="truncate">— {h}</li>
            ))}
          </ul>
        )}

        <div
          className={clsx(
            'mt-auto pt-3 border-t border-border flex items-center gap-1.5 transition-opacity motion-base',
            hovered ? 'opacity-100' : 'opacity-0 group-focus-within:opacity-100',
          )}
        >
          {onSave && (
            <button
              type="button"
              onClick={() => onSave(school.id)}
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
              onClick={() => onCompare(school.id)}
              aria-label={inCompare ? 'Remove from compare' : 'Add to compare'}
              className={clsx(
                'inline-flex items-center justify-center h-9 px-2 rounded-md text-[13px] font-bold motion-fast transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
                inCompare
                  ? 'bg-[#2A6BD4] text-[#FCFAF2] dark:bg-[#6FA0E8] dark:text-[#0A1428]'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              Compare
            </button>
          )}
          {onOpen && (
            <button
              type="button"
              onClick={() => onOpen(school.id)}
              aria-label={`Open ${school.name}`}
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
