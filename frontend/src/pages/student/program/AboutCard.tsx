import { ExternalLink, BookOpen } from 'lucide-react'
import Card from '../../../components/ui/Card'

interface Props {
  description: string
}

/** Extract likely key terms from a paragraph: capitalized noun phrases, quoted phrases. */
function extractKeywords(text: string): string[] {
  if (!text) return []
  const cleaned = text.replace(/\[Source:.*?\]/g, '').trim()
  const candidates = new Set<string>()

  // Match capitalized multi-word phrases (e.g. "Cultural Anthropology")
  const caps = cleaned.match(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b/g) || []
  for (const c of caps) {
    // Filter out single common words like "The", "NYU"
    if (c.length > 4 && !['The', 'This', 'NYU', 'New York', 'New York City'].includes(c)) {
      candidates.add(c)
    }
  }
  return Array.from(candidates).slice(0, 5)
}

function extractSource(text: string): string | null {
  const m = text.match(/\[Source:\s*(.*?)\]/)
  return m?.[1]?.trim() || null
}

function sourceDomain(url: string): string {
  try {
    const u = new URL(url)
    return u.hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export default function AboutCard({ description }: Props) {
  if (!description) return null

  const sourceUrl = extractSource(description)
  const cleanText = description.replace(/\s*\[Source:.*?\]\s*/g, '').trim()
  const keywords = extractKeywords(cleanText)

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen size={14} className="text-student" />
        <h3 className="font-semibold text-student-ink">About This Program</h3>
      </div>

      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {keywords.map(k => (
            <span key={k} className="px-2 py-0.5 text-[10px] rounded-md bg-student-mist text-student font-medium">
              {k}
            </span>
          ))}
        </div>
      )}

      <p className="text-[13px] text-student-text leading-relaxed whitespace-pre-line">{cleanText}</p>

      {sourceUrl && (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100 hover:border-student/30 hover:bg-slate-100 transition-colors group"
        >
          <img
            src={`https://www.google.com/s2/favicons?domain=${sourceDomain(sourceUrl)}&sz=32`}
            alt=""
            className="w-4 h-4 flex-shrink-0"
            onError={e => (e.currentTarget.style.display = 'none')}
          />
          <div className="min-w-0 flex-1">
            <p className="text-[10px] text-student-text/60 uppercase tracking-wider font-medium leading-none">Source</p>
            <p className="text-[11px] text-student-ink truncate mt-0.5 group-hover:text-student">{sourceDomain(sourceUrl)}</p>
          </div>
          <ExternalLink size={12} className="text-student-text/50 group-hover:text-student flex-shrink-0" />
        </a>
      )}
    </Card>
  )
}
