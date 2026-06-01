import { Link } from 'react-router-dom'
import { Database, ChevronRight, ShieldCheck } from 'lucide-react'
import SettingsSection from './SettingsSection'

// Spec 21 §2.5 — consent + export + access log live on Profile → Data (one source
// of truth). Settings only links there; deletion lives in the Danger zone below.

export default function DataPrivacyCard() {
  return (
    <SettingsSection
      icon={Database}
      title="Data & privacy"
      description="Your consent choices, data export, and access log."
    >
      <Link
        to="/s/profile?tab=data"
        className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-4 py-3 transition-colors hover:bg-muted"
      >
        <span className="flex items-center gap-2.5 text-sm text-foreground">
          <ShieldCheck size={16} className="text-secondary" />
          Manage data rights &rarr;
        </span>
        <ChevronRight size={16} className="text-muted-foreground" />
      </Link>
    </SettingsSection>
  )
}
