import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import { startSession } from '../../api/discovery'
import usePageTitle from '../../hooks/usePageTitle'
import Button from '../../components/ui/Button'
import { Sparkles, ArrowRight } from 'lucide-react'

/**
 * Spec/04 §4.5 — thin shim: seed the first discovery session and route
 * into Discover at track=profile, layer=basic.
 */
export default function OnboardingPage() {
  const navigate = useNavigate()
  useAuthStore()
  usePageTitle('Welcome')

  const seedMut = useMutation({
    mutationFn: () => startSession('profile', 'basic'),
    onSuccess: () => navigate('/s?track=profile&layer=basic', { replace: true }),
    onError: () => navigate('/s?track=profile&layer=basic', { replace: true }),
  })

  useEffect(() => {
    seedMut.mutate()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-6">
      <div className="max-w-md w-full text-center space-y-6">
        <Sparkles size={32} className="mx-auto text-primary" />
        <div>
          <h1 className="text-h2 text-foreground mb-2">Setting up your Discover journey</h1>
          <p className="text-sm text-muted-foreground">
            We are creating your first profile conversation. This takes a moment.
          </p>
        </div>
        {seedMut.isPending && (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
        )}
        {!seedMut.isPending && (
          <Button onClick={() => navigate('/s?track=profile&layer=basic')} className="mx-auto">
            Continue to Discover <ArrowRight size={16} className="ml-1" />
          </Button>
        )}
      </div>
    </div>
  )
}
