import { ChevronDown, UserCheck, UserPlus, UserX } from 'lucide-react'
import Dropdown from '../../../components/ui/Dropdown'
import { useAuthStore } from '../../../stores/auth-store'
import type { InstThread, StaffMember } from '../../../types'

// Spec 29 §2 — thread assignment (mine / unassigned / all). MVP roster = the
// institution admin; "Assign to yourself to respond".
export default function AssignMenu({
  thread,
  roster,
  onAssign,
}: {
  thread: InstThread
  roster: StaffMember[]
  onAssign: (staffUserId: string | null) => void
}) {
  const currentUserId = useAuthStore(s => s.user?.id)
  const assignedToMe = !!currentUserId && thread.assigned_to === currentUserId

  const items = []
  if (!assignedToMe) {
    items.push({
      label: 'Assign to me',
      icon: <UserPlus size={14} />,
      onClick: () => currentUserId && onAssign(currentUserId),
    })
  }
  for (const m of roster) {
    if (m.id === currentUserId) continue
    items.push({
      label: `Assign to ${m.name}`,
      icon: <UserCheck size={14} />,
      onClick: () => onAssign(m.id),
    })
  }
  if (thread.assigned_to) {
    items.push({
      label: 'Unassign',
      icon: <UserX size={14} />,
      variant: 'danger' as const,
      onClick: () => onAssign(null),
    })
  }

  return (
    <Dropdown
      align="right"
      trigger={
        <button className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 text-xs font-medium text-foreground hover:bg-muted">
          <UserCheck size={13} className={thread.assigned_to ? 'text-secondary' : 'text-muted-foreground'} />
          {thread.assigned_to_name ? thread.assigned_to_name : 'Unassigned'}
          <ChevronDown size={12} className="text-muted-foreground" />
        </button>
      }
      items={items}
    />
  )
}
