/**
 * Discover → Artifact rail (spec 19 §6).
 *
 * Right-side panel that switches widget by active track + active layer.
 * On the Profile track the layer drives the widget so the student sees
 * the captures relevant to the question they're being asked right now:
 *   - basic       → BasicSignalsWidget       (GPA, location, education stage)
 *   - personality → PersonalitySignalsWidget (interests / passions / peer-style)
 *   - identity    → IdentitySignalsWidget    (values, worldview, self-awareness)
 */
import BasicSignalsWidget from './BasicSignalsWidget'
import GoalStackWidget from './GoalStackWidget'
import IdentitySignalsWidget from './IdentitySignalsWidget'
import NeedsMapWidget from './NeedsMapWidget'
import PersonalitySignalsWidget from './PersonalitySignalsWidget'
import type { DiscoveryLayer, DiscoveryTrack } from '../../../types'

interface Props {
  track: DiscoveryTrack
  layer?: DiscoveryLayer | null
}

function ProfileWidget({ layer }: { layer?: DiscoveryLayer | null }) {
  if (layer === 'personality') return <PersonalitySignalsWidget />
  if (layer === 'identity') return <IdentitySignalsWidget />
  return <BasicSignalsWidget />
}

export default function ArtifactRail({ track, layer }: Props) {
  return (
    <aside className="space-y-3">
      {track === 'profile' && <ProfileWidget layer={layer} />}
      {track === 'goals' && <GoalStackWidget />}
      {track === 'needs' && <NeedsMapWidget />}
    </aside>
  )
}
