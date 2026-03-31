import { forwardRef } from 'react'
import clsx from 'clsx'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  showCount?: boolean
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, helperText, showCount, maxLength, className, value, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const charCount = typeof value === 'string' ? value.length : 0

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          value={value}
          maxLength={maxLength}
          className={clsx(
            'w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-y min-h-[80px]',
            error ? 'border-red-500' : 'border-gray-300',
            className
          )}
          {...props}
        />
        <div className="flex justify-between mt-1">
          <div>
            {error && <p className="text-xs text-red-600">{error}</p>}
            {helperText && !error && <p className="text-xs text-gray-500">{helperText}</p>}
          </div>
          {showCount && maxLength && (
            <p className="text-xs text-gray-400">{charCount}/{maxLength}</p>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
export default Textarea
