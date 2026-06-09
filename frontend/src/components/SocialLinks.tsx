import type { ContentSources } from '../types'

type Social = NonNullable<ContentSources['social']>

const PLATFORMS: { key: keyof Social; label: string }[] = [
  { key: 'instagram', label: 'Instagram' },
  { key: 'linkedin', label: 'LinkedIn' },
  { key: 'x', label: 'X' },
  { key: 'youtube', label: 'YouTube' },
  { key: 'facebook', label: 'Facebook' },
]

/**
 * Row of official social-channel links (Instagram / LinkedIn / X / YouTube /
 * Facebook). Renders nothing when no handles are configured. Labeled pills
 * (no brand-icon dependency) — utilitarian, matches the dense app surfaces.
 */
export default function SocialLinks({
  social,
  className = '',
}: {
  social?: ContentSources['social'] | null
  className?: string
}) {
  if (!social) return null
  const links = PLATFORMS.filter(p => social[p.key])
  if (links.length === 0) return null
  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      {links.map(p => (
        <a
          key={p.key}
          href={social[p.key] as string}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          {p.label} ↗
        </a>
      ))}
    </div>
  )
}
