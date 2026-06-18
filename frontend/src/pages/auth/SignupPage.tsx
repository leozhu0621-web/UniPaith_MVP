import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthStore } from '../../stores/auth-store'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import GoogleSignInButton from '../../components/auth/GoogleSignInButton'

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine(d => d.password === d.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
})

type FormData = z.infer<typeof schema>

export default function SignupPage() {
  const navigate = useNavigate()
  const signup = useAuthStore(s => s.signup)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    setLoading(true)
    try {
      await signup(data.email, data.password, 'student')
      navigate('/onboarding')
    } catch (err: any) {
      const raw = String(err?.message || '')
      const isDuplicate = /already exists|already registered|duplicate|409/i.test(raw)
      setError(
        isDuplicate
          ? 'An account with this email already exists. Try logging in.'
          : 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-semibold text-foreground mb-1">Create your student account</h2>

      {error && (
        <div role="alert" aria-live="assertive" className="bg-error-soft border border-error/30 text-error text-sm px-4 py-2 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Email"
          type="email"
          {...register('email')}
          error={errors.email?.message}
        />
        <Input
          label="Password"
          type="password"
          {...register('password')}
          error={errors.password?.message}
          helperText="8+ characters"
        />
        <Input
          label="Confirm password"
          type="password"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
        />

        <Button type="submit" loading={loading} className="w-full">
          Create account
        </Button>
      </form>

      <GoogleSignInButton label="Continue with Google" />

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="text-secondary font-semibold hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}
