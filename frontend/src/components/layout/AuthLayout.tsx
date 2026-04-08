interface Props { children: React.ReactNode }

export default function AuthLayout({ children }: Props) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">
            <span className="text-brand-slate-600">Uni</span><span className="text-brand-slate-800 font-extrabold">Paith</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">Smart Admissions Platform</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {children}
        </div>
      </div>
    </div>
  )
}
