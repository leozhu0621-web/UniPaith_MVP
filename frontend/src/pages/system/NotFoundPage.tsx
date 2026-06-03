import { Link } from 'react-router-dom'
import Button from '../../components/ui/Button'

// 404 — in-app "not found" surface (Spec 78 §5). Distinct from RouteErrorPage
// (render crash). Plain, honest, with a way back.
export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 text-center">
      <p className="text-eyebrow uppercase tracking-[0.22em] text-secondary font-semibold mb-2">404</p>
      <h1 className="text-2xl font-bold text-foreground mb-1">We couldn't find that.</h1>
      <p className="text-sm text-muted-foreground max-w-[48ch] mb-6">
        The page you're looking for may have moved or no longer exists.
      </p>
      <Link to="/">
        <Button variant="secondary">Go home</Button>
      </Link>
    </div>
  )
}
