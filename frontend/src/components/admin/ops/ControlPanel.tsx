import Button from '../../ui/Button'
import Card from '../../ui/Card'

interface ControlPanelProps {
  locked: boolean
  unlockExpiresInSec: number
  policy: {
    autonomy_enabled?: boolean
    auto_fix_enabled?: boolean
    emergency_stop?: boolean
  }
  busy: boolean
  onUnlock: () => void
  onLockNow: () => void
  onToggleAutonomy: () => void
  onToggleAutoFix: () => void
  onToggleEmergencyStop: () => void
  onRunLoop: () => void
  onRunEngineGraph: () => void
  onRunCrawlAll: () => void
  onRunMLCycle: () => void
  onTriggerTraining: () => void
  onDriftCheck: () => void
}

export default function ControlPanel({
  locked,
  unlockExpiresInSec,
  policy,
  busy,
  onUnlock,
  onLockNow,
  onToggleAutonomy,
  onToggleAutoFix,
  onToggleEmergencyStop,
  onRunLoop,
  onRunEngineGraph,
  onRunCrawlAll,
  onRunMLCycle,
  onTriggerTraining,
  onDriftCheck,
}: ControlPanelProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Control Panel</h3>
          <p className="text-xs text-gray-500">Read-only by default. Unlock temporarily to run controls.</p>
        </div>
        {locked ? (
          <Button size="sm" onClick={onUnlock}>Unlock Controls (5 min)</Button>
        ) : (
          <Button size="sm" variant="secondary" onClick={onLockNow}>Lock Now ({unlockExpiresInSec}s)</Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        <Button
          variant={policy?.autonomy_enabled ? 'secondary' : 'primary'}
          disabled={locked || busy}
          onClick={onToggleAutonomy}
        >
          {policy?.autonomy_enabled ? 'Disable Autonomy' : 'Enable Autonomy'}
        </Button>
        <Button
          variant={policy?.auto_fix_enabled ? 'secondary' : 'primary'}
          disabled={locked || busy}
          onClick={onToggleAutoFix}
        >
          {policy?.auto_fix_enabled ? 'Disable Auto-Fix' : 'Enable Auto-Fix'}
        </Button>
        <Button
          variant={policy?.emergency_stop ? 'primary' : 'secondary'}
          disabled={locked || busy}
          onClick={onToggleEmergencyStop}
        >
          {policy?.emergency_stop ? 'Clear Emergency Stop' : 'Emergency Stop'}
        </Button>
        <Button disabled={locked || busy} onClick={onRunLoop}>Run Self-Driving Tick</Button>
        <Button variant="secondary" disabled={locked || busy} onClick={onRunEngineGraph}>Run Full Engine Graph</Button>
        <Button variant="secondary" disabled={locked || busy} onClick={onRunCrawlAll}>Run Crawl All</Button>
        <Button variant="secondary" disabled={locked || busy} onClick={onRunMLCycle}>Run ML Full Cycle</Button>
        <Button variant="secondary" disabled={locked || busy} onClick={onTriggerTraining}>Trigger Training</Button>
        <Button variant="secondary" disabled={locked || busy} onClick={onDriftCheck}>Run Drift Check</Button>
      </div>
    </Card>
  )
}
