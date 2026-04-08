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
      const dest = user?.role === 'admin' ? '/admin'
        : user?.role === 'student' ? '/s/chat'
        : '/i/dashboard'
      navigate(dest)
    } catch (err: any) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  const googleSignup = () => {
    const cognitoDomain = import.meta.env.VITE_COGNITO_DOMAIN || 'unipaith.auth.us-east-1.amazoncognito.com'
    const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID || '3fo4t4114fr9opag803jdpbits'
    const redirectUri = `${window.location.origin}/auth/callback`
    const state = `role:${role}`
    const url = `https://${cognitoDomain}/oauth2/authorize?client_id=${clientId}&response_type=code&scope=openid+email+profile&redirect_uri=${encodeURIComponent(redirectUri)}&identity_provider=Google&state=${encodeURIComponent(state)}`
    window.location.href = url
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-center mb-2">Create Account</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        {[
          { value: 'student', label: 'Student', icon: GraduationCap, sub: "I'm looking for programs" },
          { value: 'institution_admin', label: 'Institution', icon: Building2, sub: "I'm recruiting students" },
        ].map(opt => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setRole(opt.value)}
            className={clsx(
              'flex-1 p-3 rounded-lg border text-center transition-colors',
              role === opt.value
                ? 'border-gray-900 bg-gray-50'
                : 'border-gray-200 hover:border-gray-300'
            )}
          >
            <opt.icon size={20} className="mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">{opt.label}</div>
            <div className="text-xs text-gray-500">{opt.sub}</div>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={googleSignup}
        className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
      >
        <svg width="18" height="18" viewBox="0 0 24 24">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Sign up with Google
      </button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-white px-3 text-gray-400">or sign up with email</span>
        </div>
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

      <p className="text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-gray-900 font-medium hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}
