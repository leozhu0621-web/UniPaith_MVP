import { forwardRef } from 'react'
import clsx from 'clsx'
import { fieldBaseClasses, fieldStateClasses, FieldLabel } from './Input'

// Textarea — Spec/02-design-system.md §4. Multi-line; auto-grows up to ~8 rows.
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  success?: string
  helperText?: string
  showCount?: boolean
  required?: boolean
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, success, helperText, showCount, maxLength, className, value, id, required, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const helperId = inputId ? `${inputId}-help` : undefined
    const charCount = typeof value === 'string' ? value.length : 0

    return (
      <div className="w-full">
        {label && <FieldLabel htmlFor={inputId} required={required}>{label}</FieldLabel>}
        <textarea
          ref={ref}
          id={inputId}
          value={value}
          maxLength={maxLength}
          aria-invalid={error ? true : undefined}
          aria-describedby={helperId}
          aria-required={required || undefined}
          className={clsx(
            fieldBaseClasses,
            fieldStateClasses(error, success),
            'px-3 py-2 text-sm resize-y min-h-[80px] leading-relaxed',
            className
          )}
          {...props}
        />
        <div id={helperId} className="flex justify-between gap-2 min-h-[18px] mt-1">
          <div>
            {error ? (
              <p className="text-xs text-error">{error}</p>
            ) : success ? (
              <p className="text-xs text-success">{success}</p>
            ) : helperText ? (
              <p className="text-xs text-muted-foreground">{helperText}</p>
            ) : null}
          </div>
          {showCount && maxLength && (
            <p className={clsx('text-xs shrink-0', charCount >= maxLength ? 'text-error' : 'text-muted-foreground')}>
              {charCount}/{maxLength}
            </p>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
export default Textarea
