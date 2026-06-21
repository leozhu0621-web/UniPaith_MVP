import { type ReactNode, useId } from 'react'
import clsx from 'clsx'

interface TooltipProps {
  children: ReactNode
  content: ReactNode
  side?: 'top' | 'bottom'
  align?: 'start' | 'center' | 'end'
  className?: string
  contentClassName?: string
  disabled?: boolean
}

const SIDE_CLASSES: Record<NonNullable<TooltipProps['side']>, string> = {
  top: 'bottom-[calc(100%+0.5rem)]',
  bottom: 'top-[calc(100%+0.5rem)]',
}

const ALIGN_CLASSES: Record<NonNullable<TooltipProps['align']>, string> = {
  start: 'left-0',
  center: 'left-1/2 -translate-x-1/2',
  end: 'right-0',
}

export default function Tooltip({
  children,
  content,
  side = 'top',
  align = 'center',
  className,
  contentClassName,
  disabled = false,
}: TooltipProps) {
  const id = useId()

  if (disabled || !content) return <>{children}</>

  return (
    <span className={clsx('group/tooltip relative inline-flex', className)}>
      <span
        tabIndex={0}
        aria-describedby={id}
        className="inline-flex rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background"
      >
        {children}
      </span>
      <span
        id={id}
        role="tooltip"
        className={clsx(
          'pointer-events-none absolute z-50 w-max max-w-[min(18rem,calc(100vw-2rem))] whitespace-normal break-words rounded-md border border-border bg-popover px-2.5 py-1.5 text-left text-xs leading-5 text-popover-foreground elev-raised opacity-0 transition-opacity duration-150 motion-reduce:transition-none',
          'group-hover/tooltip:opacity-100 group-focus-within/tooltip:opacity-100',
          SIDE_CLASSES[side],
          ALIGN_CLASSES[align],
          contentClassName,
        )}
      >
        {content}
      </span>
    </span>
  )
}
