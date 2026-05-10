/**
 * Discover → Artifact rail.
 *
 * Right-side panel that switches widget by active track. Live-updates as
 * the chat extracts signals into the underlying tables.
 */
import GoalStackWidget from './GoalStackWidget'
import IdentitySignalsWidget from './IdentitySignalsWidget'
import NeedsMapWidget from './NeedsMapWidget'
import type { DiscoveryTrack } from '../../../types'

export default function ArtifactRail({ track }: { track: DiscoveryTrack }) {
  return (
    <aside className="space-y-3">
      {track === 'profile' && <IdentitySignalsWidget />}
      {track === 'goals' && <GoalStackWidget />}
      {track === 'needs' && <NeedsMapWidget />}
    </aside>
  )
}
