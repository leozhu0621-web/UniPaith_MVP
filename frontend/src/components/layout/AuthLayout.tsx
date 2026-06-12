import Wordmark from '../ui/Wordmark'

interface Props { children: React.ReactNode }

export default function AuthLayout({ children }: Props) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <Wordmark className="h-14 w-auto" />
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-6">
          {children}
        </div>
      </div>
    </div>
  )
}
