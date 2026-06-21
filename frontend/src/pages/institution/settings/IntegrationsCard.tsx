import { Link } from 'react-router-dom'
import { Plug, Database, ChevronRight, Mail } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
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

      {/* SIS / CRM connectors */}
      <div className="pt-3">
        <div className="mb-2 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              SIS &amp; CRM connectors
            </p>
            <p className="text-xs text-muted-foreground">
              Use CSV upload and exports for this release. Connector credentials are configured by UniPaith support.
            </p>
          </div>
          <Link
            to="/i/data"
            className="self-start text-xs font-semibold text-secondary underline-offset-4 hover:underline sm:self-auto"
          >
            Open data upload
          </Link>
        </div>
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
              <Badge variant="neutral">Not connected</Badge>
            </div>
          ))}
        </div>
      </div>
    </SettingsSection>
  )
}
