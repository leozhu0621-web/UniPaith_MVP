import type { ReactNode } from 'react'

/** Lightweight inline markdown — links + bold only (Spec 22 §4 / 27 §2). */
export function renderInlineMarkdown(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-charcoal">{part.slice(2, -2)}</strong>
    }
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link) {
      return (
        <a key={i} href={link[2]} target="_blank" rel="noopener noreferrer" className="text-cobalt hover:underline">
          {link[1]}
        </a>
      )
    }
    return part
  })
}
