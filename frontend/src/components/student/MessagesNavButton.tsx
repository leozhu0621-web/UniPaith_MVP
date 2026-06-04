import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare } from 'lucide-react'
import { getThreads } from '../../api/inbox'

// Messages as a top-level nav affordance (LinkedIn-style) — surfaces what was a
// sub-tab under Apply, with a live unread badge so new institution messages are
// visible from anywhere. Self-contained so the layout diff stays minimal.
export default function MessagesNavButton() {
  const { data } = useQuery({
    queryKey: ['inbox-threads-unread'],
    queryFn: () => getThreads(),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
  const count = Array.isArray(data) ? data.filter((t) => t.unread).length : 0
  return (
    <Link
      to="/s/manage?tab=messages"
      aria-label={count ? `Messages, ${count} unread` : 'Messages'}
      className="ui-btn relative p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      <MessageSquare size={20} strokeWidth={1.75} />
      {count > 0 && (
        <span
          className="absolute -right-0.5 -top-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-secondary px-1 text-[10px] font-semibold leading-none text-secondary-foreground"
          aria-hidden
        >
          {count > 9 ? '9+' : count}
        </span>
      )}
    </Link>
  )
}
