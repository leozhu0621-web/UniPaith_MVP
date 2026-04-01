import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
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
  const login = useAuthStore(s => s.login)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    setLoading(true)
    // #region agent log
    fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'5ae59b'},body:JSON.stringify({sessionId:'5ae59b',runId:'initial',hypothesisId:'H1',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:start:v2',message:'Login submit entered',data:{hasEmail:Boolean(data.email),passwordLength:data.password?.length??0},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    // #region agent log
    fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H1',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:start',message:'Login form submitted',data:{emailDomain:data.email.includes('@')?data.email.split('@')[1]:'invalid'},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    try {
      await login(data.email, data.password)
      const user = useAuthStore.getState().user
      const dest = user?.role === 'admin' ? '/admin'
        : user?.role === 'student' ? '/s/chat'
        : '/i/dashboard'
      // #region agent log
      fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'5ae59b'},body:JSON.stringify({sessionId:'5ae59b',runId:'initial',hypothesisId:'H4',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:success:v2',message:'Login submit success branch',data:{hasUser:Boolean(user),role:user?.role??null,destination:dest},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      // #region agent log
      fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H4',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:success',message:'Login completed and navigation chosen',data:{isUserPresent:Boolean(user),role:user?.role??null,destination:dest},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      navigate(dest)
    } catch (err: any) {
      // #region agent log
      fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'5ae59b'},body:JSON.stringify({sessionId:'5ae59b',runId:'initial',hypothesisId:'H2',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:catch:v2',message:'Login submit catch branch',data:{errorMessage:err?.message??'unknown'},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      // #region agent log
      fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H1',location:'frontend/src/pages/auth/LoginPage.tsx:onSubmit:catch',message:'Login handler caught error',data:{errorMessage:err?.message??'unknown'},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <h2 className="text-xl font-semibold text-center mb-2">Log in</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded">
          {error}
        </div>
      )}

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

      <p className="text-center text-sm text-gray-500">
        Don't have an account?{' '}
        <Link to="/signup" className="text-gray-900 font-medium hover:underline">
          Sign up
        </Link>
      </p>
    </form>
  )
}
