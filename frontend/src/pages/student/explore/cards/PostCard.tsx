import { useState, type ReactNode } from 'react'
import { ChevronDown, ChevronUp, GraduationCap, Megaphone, Pin } from 'lucide-react'
import type { InstitutionPost } from '../../../../types'

interface Props {
  post: InstitutionPost
}

/** Lightweight inline markdown — links + bold only (Spec 22 §4). */
function renderInlineMarkdown(text: string): ReactNode[] {
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

/** Institution update card — Spec 22 §4 / §12. Editorial cobalt shell; gold pin marker. */
export default function PostCard({ post }: Props) {
  const [expanded, setExpanded] = useState(false)
  const body = post.body || ''
  const isLong = body.length > 220
  const shown = expanded || !isLong ? body : `${body.slice(0, 220).trimEnd()}…`

  return (
    <div
      className={`bg-white rounded-xl border hover:shadow-sm transition-shadow overflow-hidden ${
        post.pinned ? 'border-gold' : 'border-stone'
      }`}
    >
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Megaphone size={12} className="text-cobalt" />
        <span className="text-[10px] font-semibold text-cobalt uppercase tracking-wider">Update</span>
        {post.pinned && (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-gold-hover ml-1">
            <Pin size={11} className="fill-gold text-gold" /> Pinned
          </span>
        )}
        <span className="text-[10px] text-slate ml-auto">
          {new Date(post.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-md bg-cobalt/10 flex items-center justify-center">
            <GraduationCap size={14} className="text-cobalt" />
          </div>
          <span className="text-xs font-semibold text-charcoal">{(post as any).institution_name || 'School'}</span>
        </div>
        <h3 className="text-sm font-semibold text-charcoal mb-1">{post.title}</h3>
        <p className="text-xs text-slate line-clamp-none leading-relaxed whitespace-pre-line">
          {renderInlineMarkdown(shown)}
        </p>
        {post.program_names && post.program_names.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {post.program_names.map(name => (
              <span
                key={name}
                className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-full bg-cobalt/10 text-cobalt border border-cobalt/20"
              >
                {name}
              </span>
            ))}
          </div>
        )}
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded(e => !e)}
            className="inline-flex items-center gap-0.5 text-[11px] font-medium text-cobalt mt-1"
          >
            {expanded ? <>Show less <ChevronUp size={12} /></> : <>Read more <ChevronDown size={12} /></>}
          </button>
        )}
        {post.media_urls && post.media_urls.length > 0 && (
          <div className="mt-2 flex gap-2 overflow-x-auto">
            {post.media_urls.slice(0, 3).map((m: any, i: number) => (
              <div key={i} className="w-24 h-16 rounded-lg bg-muted overflow-hidden flex-shrink-0">
                <img src={typeof m === 'string' ? m : m.url} alt="" className="w-full h-full object-cover" onError={e => (e.currentTarget.style.display = 'none')} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
