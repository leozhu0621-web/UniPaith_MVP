import { Link } from 'react-router-dom'
import { GraduationCap, Building2 } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">UniPaith</h1>
      <p className="text-lg text-gray-500 mb-12">AI-Powered Admissions</p>

      <div className="flex gap-6 max-w-2xl w-full">
        <Link
          to="/signup?role=student"
          className="flex-1 bg-white rounded-xl border border-gray-200 p-8 hover:shadow-lg hover:border-gray-300 transition-all text-center group"
        >
          <GraduationCap size={40} className="mx-auto mb-4 text-gray-400 group-hover:text-gray-900 transition-colors" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">I'm a Student</h2>
          <p className="text-sm text-gray-500">Get matched with your ideal programs</p>
        </Link>

        <Link
          to="/signup?role=institution_admin"
          className="flex-1 bg-white rounded-xl border border-gray-200 p-8 hover:shadow-lg hover:border-gray-300 transition-all text-center group"
        >
          <Building2 size={40} className="mx-auto mb-4 text-gray-400 group-hover:text-gray-900 transition-colors" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">I'm an Institution</h2>
          <p className="text-sm text-gray-500">Find your best-fit students</p>
        </Link>
      </div>

      <p className="mt-8 text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-gray-900 font-medium hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}
