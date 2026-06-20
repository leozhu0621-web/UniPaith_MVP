import { useSearchParams } from 'react-router-dom'

import MessagesPage from '../MessagesPage'

export default function MessagesRoom() {
  const [searchParams] = useSearchParams()
  return (
    <div className="h-full min-h-[min(100dvh-8rem,760px)] lg:min-h-[calc(100dvh-4rem)]">
      <MessagesPage initialThreadId={searchParams.get('thread')} />
    </div>
  )
}
