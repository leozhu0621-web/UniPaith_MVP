// Authored reference content for the Resources tab guides (Spec 2026-06-14).
// These are general, accurate explainers — NOT personalized claims and NOT
// fabricated numbers/deadlines. Each guide ships a standing "confirm with the
// school / official sources" note rendered by GuideSections.
import type { LucideIcon } from 'lucide-react'

export interface GuideSection {
  id: string
  icon: LucideIcon
  heading: string
  body: string
  bullets?: string[]
}
