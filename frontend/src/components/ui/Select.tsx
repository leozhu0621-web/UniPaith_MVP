// Select — Spec/02-design-system.md §4.
// Native select for ≤7 options. For ≥8 or async-fetched, use a combobox
// (custom; future).

import { forwardRef, useId } from 'react'
import clsx from 'clsx'
import { ChevronDown } from 'lucide-react'

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  helperText?: string
  options: { value: string; label: string }[]
  placeholder?: string
  required?: boolean
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    { label, error, helperText, options, placeholder, className, id, required, ...props },
    ref,
  ) => {
    const autoId = useId()
    const inputId = id || `select-${autoId}`
    const helperId = `${inputId}-helper`
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
        <div className="relative">
          <select
            ref={ref}
            id={inputId}
            required={required}
            aria-required={required || undefined}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={helperContent ? helperId : undefined}
            className={clsx(
              'w-full appearance-none rounded-[12px] bg-card text-foreground',
              'h-10 pl-3 pr-9 text-base border motion-base transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] focus-visible:border-[#2A6BD4]',
              'disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed',
              error
                ? 'border-[#B5321F] bg-[#F2D7D0]/40 dark:border-[#FF8470] dark:bg-[#3D1E1A]/40'
                : 'border-border hover:border-foreground/40',
              className,
            )}
            {...props}
          >
            {placeholder && <option value="">{placeholder}</option>}
            {options.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <ChevronDown
            size={16}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
          />
        </div>
        <p
          id={helperId}
          className={clsx(
            'mt-1.5 text-[13px] min-h-[18px]',
            error ? 'text-[#B5321F] dark:text-[#FF8470]' : 'text-muted-foreground',
          )}
        >
          {helperContent || ' '}
        </p>
      </div>
    )
  },
)

Select.displayName = 'Select'
export default Select
