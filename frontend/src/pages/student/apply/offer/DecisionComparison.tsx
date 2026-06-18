import Modal from '../../../../components/ui/Modal'
import OfferComparisonTable from './OfferComparisonTable'

/**
 * Modal wrapper around the offer comparison table. The table is the source
 * of truth (also rendered inline in the Offers view); this keeps the modal
 * entry points (OfferPanel, the Applications "all"-view banner) working with
 * a lazy-on-open fetch.
 */
export default function DecisionComparison({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Compare your offers" size="lg">
      <OfferComparisonTable enabled={isOpen} onNavigate={onClose} />
    </Modal>
  )
}
