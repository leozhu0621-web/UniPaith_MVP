/**
 * Living-profile slide-over drawer — the overlay/mobile home of
 * LivingProfilePanel. On desktop the same panel is docked in the Uni rail
 * (JourneyRail). The query runs only while the drawer is open.
 */
import Sheet from '../../../components/ui/Sheet'
import LivingProfilePanel from './LivingProfilePanel'

export default function ProfileDrawer({
  isOpen,
  onClose,
  onAsk,
}: {
  isOpen: boolean
  onClose: () => void
  /** Drop a gap-invitation prompt into the conversation. */
  onAsk?: (prompt: string) => void
}) {
  return (
    <Sheet isOpen={isOpen} onClose={onClose} title="Your profile" side="right">
      <LivingProfilePanel enabled={isOpen} onAsk={onAsk} onNavigate={onClose} />
    </Sheet>
  )
}
