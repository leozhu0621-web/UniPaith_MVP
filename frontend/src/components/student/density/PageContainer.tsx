import clsx from 'clsx'

// PageContainer — platform UX overhaul Ship A (2026-06-12 spec §1).
// The single app-shell page recipe: full-bleed width, standard gutters,
// page-entrance motion. Editorial detail pages (max-w-5xl) do NOT use this.
// Mobile bottom-tab-bar clearance is handled by the StudentLayout Outlet
// wrapper, not here.
interface PageContainerProps {
  children: React.ReactNode
  className?: string
}

export default function PageContainer({ children, className }: PageContainerProps) {
  return <div className={clsx('w-full px-4 sm:px-6 py-5 animate-page-in', className)}>{children}</div>
}
