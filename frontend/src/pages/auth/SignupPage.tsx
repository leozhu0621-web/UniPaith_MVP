import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthStore } from '../../stores/auth-store'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import clsx from 'clsx'
import { GraduationCap, Building2 } from 'lucide-react'

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
  const [searchParams] = useSearchParams()
  const signup = useAuthStore(s => s.signup)
  const [role, setRole] = useState<string>(searchParams.get('role') || 'student')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    setLoading(true)
    try {
      await signup(data.email, data.password, role)
      const user = useAuthStore.getState().user
      const dest = user?.role === 'student' ? '/onboarding' : '/i/dashboard'
      navigate(dest)
    } catch (err: any) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-center text-foreground mb-2">Create your account</h2>

      {error && (
        <div className="bg-error-soft border border-error/30 text-error text-sm px-4 py-2 rounded-lg">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        {[
          { value: 'student', label: 'Student', icon: GraduationCap, sub: 'Everyone’s private college counselor' },
          { value: 'institution_admin', label: 'Institution', icon: Building2, sub: 'The admission operating system' },
        ].map(opt => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setRole(opt.value)}
            className={clsx(
              'flex-1 p-3 rounded-lg border text-center transition-colors',
              role === opt.value
                ? 'border-secondary bg-secondary/5'
                : 'border-border hover:border-secondary/40'
            )}
          >
            <opt.icon size={20} className={clsx('mx-auto mb-1', role === opt.value ? 'text-secondary' : 'text-muted-foreground')} />
            <div className="text-sm font-semibold text-foreground">{opt.label}</div>
            <div className="text-xs text-muted-foreground">{opt.sub}</div>
          </button>
        ))}
      </div>

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
          label="Confirm Password"
          type="password"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
        />

        <Button type="submit" loading={loading} className="w-full">
          Create Account
        </Button>
      </form>

      {role === 'student' && (
        <p className="text-center text-xs text-muted-foreground">7 days free, then $15/mo. Cancel anytime.</p>
      )}

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="text-secondary font-semibold hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}
