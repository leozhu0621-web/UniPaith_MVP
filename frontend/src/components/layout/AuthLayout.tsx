interface Props { children: React.ReactNode }

export default function AuthLayout({ children }: Props) {
  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/wordmark.svg" alt="UniPaith" className="h-10 w-auto mx-auto" />
          <p className="text-slate text-sm mt-3">Find programs. Find applicants.</p>
        </div>
        <div className="bg-white rounded-lg shadow-subtle border border-stone/60 p-6">
          {children}
        </div>
      </div>
    </div>
  )
}
