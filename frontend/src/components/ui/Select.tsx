import { forwardRef } from 'react'
import clsx from 'clsx'
import { ChevronDown } from 'lucide-react'
import { fieldBaseClasses, fieldStateClasses, FieldLabel, FieldHelp } from './Input'

// Select — Spec/02-design-system.md §4. Native select for ≤7 options.
type FieldSize = 'sm' | 'md' | 'lg'

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string
  error?: string
  success?: string
  helperText?: string
  options: { value: string; label: string }[]
  placeholder?: string
  uiSize?: FieldSize
  required?: boolean
}

const SIZE_CLASSES: Record<FieldSize, string> = {
  sm: 'h-8 text-[13px]',
  md: 'h-10 text-sm',
  lg: 'h-12 text-base',
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, success, helperText, options, placeholder, uiSize = 'md', className, id, required, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const helperId = inputId ? `${inputId}-help` : undefined
    return (
      <div className="w-full">
        {label && <FieldLabel htmlFor={inputId} required={required}>{label}</FieldLabel>}
        <div className="relative">
          <select
            ref={ref}
            id={inputId}
            aria-invalid={error ? true : undefined}
            aria-describedby={helperId}
            aria-required={required || undefined}
            className={clsx(
              fieldBaseClasses,
              fieldStateClasses(error, success),
              SIZE_CLASSES[uiSize],
              'appearance-none pl-3 pr-9 cursor-pointer',
              className
            )}
            {...props}
          >
            {placeholder && <option value="">{placeholder}</option>}
            {options.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>
        <div id={helperId}>
          <FieldHelp error={error} success={success} helperText={helperText} />
        </div>
      </div>
    )
  }
)

Select.displayName = 'Select'
export default Select
