import { useToastStore, type ToastType } from '../../stores/toast-store'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import clsx from 'clsx'

const ICON_MAP: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle size={16} className="text-green-500" />,
  error: <AlertCircle size={16} className="text-red-500" />,
  warning: <AlertTriangle size={16} className="text-yellow-500" />,
  info: <Info size={16} className="text-blue-500" />,
}

const BG_MAP: Record<ToastType, string> = {
  success: 'border-green-200 bg-green-50',
  error: 'border-red-200 bg-red-50',
  warning: 'border-yellow-200 bg-yellow-50',
  info: 'border-blue-200 bg-blue-50',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={clsx(
            'flex items-start gap-2 px-4 py-3 rounded-lg border shadow-md animate-in slide-in-from-right',
            BG_MAP[toast.type]
          )}
        >
          <span className="mt-0.5">{ICON_MAP[toast.type]}</span>
          <p className="flex-1 text-sm text-gray-800">{toast.message}</p>
          <button onClick={() => removeToast(toast.id)} className="p-0.5 hover:bg-black/5 rounded">
            <X size={14} className="text-gray-500" />
          </button>
        </div>
      ))}
    </div>
  )
}
