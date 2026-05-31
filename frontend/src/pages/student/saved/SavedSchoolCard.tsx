import { GraduationCap, MapPin, X } from 'lucide-react'
import type { FollowedInstitution } from '../../../api/events'

interface Props {
  school: FollowedInstitution
  onOpen: () => void
  onUnfollow?: () => void
  unfollowing?: boolean
}

export default function SavedSchoolCard({ school, onOpen, onUnfollow, unfollowing }: Props) {
  return (
    <div className="bg-card rounded-xl border border-border elev-subtle hover:elev-raised transition-shadow overflow-hidden flex flex-col">
      <button type="button" onClick={onOpen} className="flex-1 text-left p-4 flex gap-3 min-w-0">
        <div className="w-11 h-11 rounded-lg bg-muted border border-stone/60 flex items-center justify-center flex-shrink-0">
          <GraduationCap size={18} className="text-secondary" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-[15px] font-bold text-charcoal leading-snug truncate">{school.name}</h3>
          <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1">
            <MapPin size={10} className="flex-shrink-0" />
            Saved school · updates in Connect
          </p>
        </div>
      </button>
      {onUnfollow && (
        <div className="border-t border-border px-3 py-2 flex justify-end">
          <button
            type="button"
            onClick={e => {
              e.stopPropagation()
              onUnfollow()
            }}
            disabled={unfollowing}
            className="text-[11px] font-medium text-muted-foreground hover:text-error inline-flex items-center gap-1 disabled:opacity-50"
          >
            <X size={12} />
            Unfollow
          </button>
        </div>
      )}
    </div>
  )
}
