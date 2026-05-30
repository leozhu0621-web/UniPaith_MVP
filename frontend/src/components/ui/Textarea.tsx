// Textarea — Spec/02-design-system.md §4.
// Auto-grow up to 8 rows then scroll. Same chrome as Input. Char count
// optional. Helper region reserves min-height to prevent shift.

import { forwardRef, useId } from 'react'
import clsx from 'clsx'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  showCount?: boolean
  required?: boolean
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      showCount,
      maxLength,
      className,
      value,
      id,
      required,
      ...props
    },
    ref,
  ) => {
    const autoId = useId()
    const inputId = id || `textarea-${autoId}`
    const helperId = `${inputId}-helper`
    const charCount = typeof value === 'string' ? value.length : 0
    const helperContent = error || helperText

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-[13px] font-bold text-foreground/80 mb-1.5"
          >
            {label}
            {required && <span className="text-[#B5321F] dark:text-[#FF8470] ml-0.5" aria-hidden="true">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          value={value}
          maxLength={maxLength}
          required={required}
          aria-required={required || undefined}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={helperContent || showCount ? helperId : undefined}
          className={clsx(
            'w-full rounded-[12px] bg-card text-foreground placeholder:text-muted-foreground',
            'border px-3 py-2 text-base min-h-[88px] resize-y',
            'motion-base transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] focus-visible:border-[#2A6BD4]',
            'disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed',
            error
              ? 'border-[#B5321F] bg-[#F2D7D0]/40 dark:border-[#FF8470] dark:bg-[#3D1E1A]/40'
              : 'border-border hover:border-foreground/40',
            className,
          )}
          {...props}
        />
        <div id={helperId} className="flex justify-between items-start mt-1.5 min-h-[18px] text-[13px]">
          <p
            className={clsx(
              error ? 'text-[#B5321F] dark:text-[#FF8470]' : 'text-muted-foreground',
            )}
          >
            {helperContent || ' '}
          </p>
          {showCount && maxLength != null && (
            <p
              className={clsx(
                'tabular-nums flex-shrink-0 ml-2',
                charCount > maxLength * 0.9
                  ? 'text-[#B8741D] dark:text-[#F0B964]'
                  : 'text-muted-foreground',
              )}
            >
              {charCount}/{maxLength}
            </p>
          )}
        </div>
      </div>
    )
  },
)

Textarea.displayName = 'Textarea'
export default Textarea
