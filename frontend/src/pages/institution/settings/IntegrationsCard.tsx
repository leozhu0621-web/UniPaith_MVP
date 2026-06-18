import { Link } from 'react-router-dom'
import { Plug, Database, ChevronRight, Mail } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import SettingsSection from '../../student/settings/SettingsSection'

// Spec 21 §3.4 — credentials for SIS/CRM + webhooks are Phase-2 (Spec 49);
// SES sender status (Spec 25) + dataset access (Spec 24) surface here.

const CONNECTORS = [
  { name: 'Slate', kind: 'CRM' },
  { name: 'Salesforce', kind: 'CRM' },
  { name: 'Banner', kind: 'SIS' },
  { name: 'Workday', kind: 'SIS' },
]

export default function IntegrationsCard({ primaryDomain }: { primaryDomain: string | null }) {
  return (
    <SettingsSection icon={Plug} title="Integrations">
      {/* SES sender domain */}
      <div className="flex items-center justify-between gap-3 py-3 border-b border-border">
        <div className="flex items-start gap-3 min-w-0">
          <Mail size={16} className="text-secondary mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground">Email sending domain</p>
            <p className="text-xs text-muted-foreground truncate">
              {primaryDomain ?? 'Set a website to derive your domain'}
            </p>
          </div>
        </div>
        <Badge variant="neutral">Managed by UniPaith</Badge>
      </div>

      {/* Dataset access / export */}
      <Link
        to="/i/data"
        className="flex items-center justify-between gap-3 py-3 border-b border-border group"
      >
        <div className="flex items-start gap-3">
          <Database size={16} className="text-secondary mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-foreground">Data upload &amp; exports</p>
            <p className="text-xs text-muted-foreground">Manage datasets and download exports.</p>
          </div>
        </div>
        <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
      </Link>

      {/* SIS / CRM connectors — Phase 2 */}
      <div className="pt-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
          SIS &amp; CRM connectors
        </p>
        <div className="grid gap-2 sm:grid-cols-2">
          {CONNECTORS.map(c => (
            <div
              key={c.name}
              className="flex items-center justify-between gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2.5"
            >
              <div>
                <p className="text-sm font-medium text-foreground">{c.name}</p>
                <p className="text-xs text-muted-foreground">{c.kind}</p>
              </div>
              <Button variant="tertiary" size="sm" disabled>
                Coming soon
              </Button>
            </div>
          ))}
        </div>
      </div>
    </SettingsSection>
  )
}
