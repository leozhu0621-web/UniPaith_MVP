import { Link } from 'react-router-dom'
import Button from '../../components/ui/Button'

// 403 — permission-denied surface (Spec 78 §5). Shown on a role/guard mismatch
// instead of a blank screen.
export default function NoAccessPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 text-center">
      <p className="text-eyebrow uppercase tracking-[0.22em] text-secondary font-semibold mb-2">403</p>
      <h1 className="text-2xl font-bold text-foreground mb-1">You don't have access to this.</h1>
      <p className="text-sm text-muted-foreground max-w-[48ch] mb-6">
        Your account doesn't have permission to view this page. If you think this is a mistake, contact support.
      </p>
      <Link to="/">
        <Button variant="secondary">Go home</Button>
      </Link>
    </div>
  )
}
