// Input — Spec/02-design-system.md §4.
// Brand-tokened text input. Label sits above (not placeholder-as-label).
// Helper text region reserves min-height so error appearance doesn't
// shift layout. Error/success states use status tokens. Required marks
// a literal `*` (not color alone) for a11y.

import { forwardRef, useId } from 'react'
import clsx from 'clsx'

export type InputSize = 'sm' | 'md' | 'lg'

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  successText?: string
  inputSize?: InputSize
  iconLeft?: React.ReactNode
  required?: boolean
}

const SIZE_CLASSES: Record<InputSize, string> = {
  sm: 'h-8 text-[13px]',
  md: 'h-10 text-base',
  lg: 'h-12 text-base',
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      successText,
      inputSize = 'md',
      iconLeft,
      required,
      className,
      id,
      ...props
    },
    ref,
  ) => {
    const autoId = useId()
    const inputId = id || `input-${autoId}`
    const helperId = `${inputId}-helper`
    const helperContent = error || successText || helperText

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
          {iconLeft && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
              {iconLeft}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            required={required}
            aria-required={required || undefined}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={helperContent ? helperId : undefined}
            className={clsx(
              'w-full rounded-[12px] bg-card text-foreground placeholder:text-muted-foreground',
              'border motion-base transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] focus-visible:border-[#2A6BD4]',
              'disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed',
              SIZE_CLASSES[inputSize],
              iconLeft ? 'pl-10 pr-3' : 'px-3',
              error
                ? 'border-[#B5321F] bg-[#F2D7D0]/40 dark:border-[#FF8470] dark:bg-[#3D1E1A]/40'
                : successText
                ? 'border-[#1F6B2E] dark:border-[#6FCB95]'
                : 'border-border hover:border-foreground/40',
              className,
            )}
            {...props}
          />
        </div>
        {/* Reserve helper text region — prevents layout shift on error. */}
        <p
          id={helperId}
          className={clsx(
            'mt-1.5 text-[13px] min-h-[18px]',
            error
              ? 'text-[#B5321F] dark:text-[#FF8470]'
              : successText
              ? 'text-[#1F6B2E] dark:text-[#6FCB95]'
              : 'text-muted-foreground',
          )}
        >
          {helperContent || ' '}
        </p>
      </div>
    )
  },
)

Input.displayName = 'Input'
export default Input
