import { ExternalLink, BookOpen } from 'lucide-react'
import Card from '../../../components/ui/Card'

interface Props {
  description: string
  /** Name of the institution, used to filter out institution name mentions
   *  from the extracted keyword chips (we don't want "NYU" or
   *  "Stanford University" to show as a key term for every program there). */
  institutionName?: string | null
  /** Name of the program itself, same reason as institutionName. */
  programName?: string | null
  /** Official program-page URL — rendered as a prominent outbound link so
   *  students can read the school's own in-depth description at the source. */
  websiteUrl?: string | null
}

/** Build a set of stop-phrases we should never pull out as keyword chips.
 * Generic words ("The", "This"), plus any variation of the institution name
 * and the program name (so a Columbia program doesn't get "Columbia" as a
 * chip, and an Anthropology program doesn't get "Anthropology" as a chip). */
function buildStopPhrases(institutionName?: string | null, programName?: string | null): Set<string> {
  const stop = new Set<string>(['The', 'This', 'These', 'Those', 'Our'])
  const addVariants = (s?: string | null) => {
    if (!s) return
    stop.add(s)
    // Each individual word of the name
    for (const w of s.split(/\s+/)) {
      if (w.length >= 2) stop.add(w)
    }
    // Common US abbreviation pattern: all-caps shortform (e.g., "NYU", "MIT")
    const caps = s.split(/\s+/).map(w => w[0]).filter(Boolean).join('').toUpperCase()
    if (caps.length >= 2 && caps.length <= 6) stop.add(caps)
  }
  addVariants(institutionName)
  addVariants(programName)
  return stop
}

/** Extract likely key terms from a paragraph: capitalized noun phrases. */
function extractKeywords(text: string, stopPhrases: Set<string>): string[] {
  if (!text) return []
  const cleaned = text.replace(/\[Source:.*?\]/g, '').trim()
  const candidates = new Set<string>()

  // Capitalized multi-word phrases (e.g., "Cultural Anthropology", "Liberal Arts")
  const caps = cleaned.match(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b/g) || []
  for (const c of caps) {
    if (c.length <= 4) continue
    if (stopPhrases.has(c)) continue
    // Skip if the phrase is a single word already in stop phrases
    if (c.split(/\s+/).every(w => stopPhrases.has(w))) continue
    candidates.add(c)
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

export default function AboutCard({ description, institutionName, programName, websiteUrl }: Props) {
  if (!description && !websiteUrl) return null

  const sourceUrl = extractSource(description)
  const cleanText = description.replace(/\s*\[Source:.*?\]\s*/g, '').trim()
  const stopPhrases = buildStopPhrases(institutionName, programName)
  const keywords = extractKeywords(cleanText, stopPhrases)
  // Don't render a duplicate "Source" chip when it points at the same place as
  // the official program-page link below.
  const showSource = sourceUrl && sourceUrl !== websiteUrl

  return (
    <Card pad={false} className="p-5">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen size={14} className="text-secondary" />
        <h3 className="font-semibold text-foreground">About This Program</h3>
      </div>

      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {keywords.map(k => (
            <span key={k} className="px-2 py-0.5 text-[10px] rounded-md bg-muted text-foreground border border-border/60 font-medium">
              {k}
            </span>
          ))}
        </div>
      )}

      {cleanText && <p className="text-[13px] text-foreground leading-relaxed whitespace-pre-line">{cleanText}</p>}

      {websiteUrl && (
        <a
          href={websiteUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 flex items-center gap-2 px-3 py-2.5 rounded-lg bg-secondary/5 border border-secondary/30 hover:bg-secondary/10 transition-colors group"
        >
          <BookOpen size={14} className="text-secondary flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-semibold text-foreground leading-none group-hover:text-secondary">Visit the official program page</p>
            <p className="text-[11px] text-foreground/60 truncate mt-0.5">{sourceDomain(websiteUrl)}</p>
          </div>
          <ExternalLink size={13} className="text-secondary flex-shrink-0" />
        </a>
      )}

      {showSource && (
        <a
          href={sourceUrl!}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-muted border border-border hover:border-secondary/30 hover:bg-muted/70 transition-colors group"
        >
          <div className="min-w-0 flex-1">
            <p className="text-[10px] text-foreground/60 uppercase tracking-wider font-medium leading-none">Source</p>
            <p className="text-[11px] text-foreground truncate mt-0.5 group-hover:text-secondary">{sourceDomain(sourceUrl!)}</p>
          </div>
          <ExternalLink size={12} className="text-foreground/50 group-hover:text-secondary flex-shrink-0" />
        </a>
      )}
    </Card>
  )
}
