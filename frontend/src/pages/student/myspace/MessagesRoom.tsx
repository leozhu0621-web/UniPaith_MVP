import { useSearchParams } from 'react-router-dom'
import MessagesPage from '../MessagesPage'

// My Space › Messages — thin route wrapper. MessagesPage is the fixed
// two-pane inbox (Spec 17 §2); this provides the height container the old
// /s/manage tab shell used to, and threads the ?thread deep link through.

export default function MessagesRoom() {
  const [searchParams] = useSearchParams()
  const threadId = searchParams.get('thread')

  return (
    <div className="h-full min-h-[min(100dvh-9rem,720px)] lg:min-h-[calc(100dvh-8rem)]">
      <MessagesPage initialThreadId={threadId} />
    </div>
  )
}
