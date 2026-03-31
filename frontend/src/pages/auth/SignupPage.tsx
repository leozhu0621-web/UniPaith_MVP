import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthStore } from '../../stores/auth-store'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import clsx from 'clsx'
import { errorMessage } from '../../utils/errors'
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
    } catch (err: unknown) {
      setError(errorMessage(err) || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

      <p className="text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-gray-900 font-medium hover:underline">
          Log in
        </Link>
      </p>
    </form>
  )
}
