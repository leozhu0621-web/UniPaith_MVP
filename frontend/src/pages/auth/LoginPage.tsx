import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { postLoginDestination } from '../../utils/auth-redirect'
import usePageTitle from '../../hooks/usePageTitle'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthStore } from '../../stores/auth-store'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(1, 'Password is required'),
})

type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const login = useAuthStore(s => s.login)
  usePageTitle('Log in')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    setLoading(true)
    try {
      await login(data.email, data.password)
      const user = useAuthStore.getState().user
      navigate(postLoginDestination(user?.role, searchParams))
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-center text-charcoal mb-2">Welcome back</h2>

      {error && (
        <div className="bg-error-soft border border-error/30 text-error text-sm px-4 py-2 rounded-lg">
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
        />

        <Button type="submit" loading={loading} className="w-full">
          Log in
        </Button>
      </form>

      <p className="text-center text-sm text-slate">
        Don't have an account?{' '}
        <Link to="/signup" className="text-cobalt font-semibold hover:underline">
          Sign up
        </Link>
      </p>

      <p className="text-center text-sm text-gray-400">
        <Link to="/pricing" className="hover:underline">
          View plans and pricing
        </Link>
      </p>
    </div>
  )
}
