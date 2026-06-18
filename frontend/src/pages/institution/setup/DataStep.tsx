import { Database, CheckCircle2, Upload } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import WizardFooter from './WizardFooter'

export default function DataStep({
  datasetCount,
  onOpenUpload,
  onSkip,
  onContinue,
  onBack,
  busy,
}: {
  datasetCount: number
  onOpenUpload: () => void
  onSkip: () => void
  onContinue: () => void
  onBack: () => void
  busy: boolean
}) {
  const hasData = datasetCount > 0

  return (
    <Card pad={false} className="p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-foreground">Upload data</h2>

      {hasData ? (
        <div className="mt-5 flex items-start gap-3 rounded-lg border border-success/40 bg-success-soft/40 px-4 py-3">
          <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-success" />
          <div className="text-sm">
            <p className="font-medium text-foreground">
              {datasetCount} dataset{datasetCount === 1 ? '' : 's'} uploaded
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-5 flex flex-col items-center gap-3 rounded-xl border border-dashed border-border bg-muted/30 px-6 py-8 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary/10 text-secondary">
            <Database size={22} />
          </span>
          <Button variant="secondary" onClick={onOpenUpload} className="inline-flex items-center gap-2">
            <Upload size={15} /> Upload data
          </Button>
        </div>
      )}

      <WizardFooter onBack={onBack}>
        {hasData ? (
          <Button variant="secondary" onClick={onContinue} loading={busy}>
            Continue
          </Button>
        ) : (
          <>
            <Button variant="tertiary" onClick={onSkip} loading={busy}>
              I&apos;ll do this later
            </Button>
            <Button variant="secondary" onClick={onContinue} loading={busy}>
              Continue
            </Button>
          </>
        )}
      </WizardFooter>
    </Card>
  )
}
