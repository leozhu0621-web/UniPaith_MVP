import Badge from '../../ui/Badge'
import Card from '../../ui/Card'

function toBadgeVariant(status: string | undefined): 'success' | 'warning' | 'danger' | 'neutral' {
  if (!status) return 'neutral'
  if (['ok', 'healthy', 'ready', 'running'].includes(status)) return 'success'
  if (['warning', 'degraded', 'pending'].includes(status)) return 'warning'
  if (['error', 'critical', 'failed'].includes(status)) return 'danger'
  return 'neutral'
}

interface StatusBarProps {
  snapshot: any
}

export default function StatusBar({ snapshot }: StatusBarProps) {
  const policy = snapshot?.status?.policy ?? {}
  const engineRuntime = snapshot?.processing?.engine ?? {}
  const autonomyLoop = snapshot?.processing?.autonomy_loop ?? {}
  const scheduler = snapshot?.status?.scheduler ?? {}

  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={toBadgeVariant(engineRuntime?.status)}>
          Engine {engineRuntime?.status ?? 'idle'}
        </Badge>
        <Badge variant={policy?.autonomy_enabled ? 'success' : 'neutral'}>
          {policy?.autonomy_enabled ? 'Autonomy On' : 'Autonomy Off'}
        </Badge>
        <Badge variant={policy?.auto_fix_enabled ? 'success' : 'neutral'}>
          {policy?.auto_fix_enabled ? 'Auto-Fix On' : 'Auto-Fix Off'}
        </Badge>
        <Badge variant={policy?.emergency_stop ? 'danger' : 'neutral'}>
          {policy?.emergency_stop ? 'Emergency Stop' : 'No Emergency Stop'}
        </Badge>
        <Badge variant={scheduler?.self_driving_enabled ? 'success' : 'warning'}>
          Scheduler {scheduler?.self_driving_enabled ? 'On' : 'Off'}
        </Badge>
        <Badge variant={toBadgeVariant(autonomyLoop?.last_tick_status)}>
          Last Tick {autonomyLoop?.last_tick_status ?? 'never_run'}
        </Badge>
      </div>
    </Card>
  )
}
