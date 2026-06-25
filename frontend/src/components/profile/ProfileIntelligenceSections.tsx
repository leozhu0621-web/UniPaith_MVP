import type { ProfileIntelligence, ProfileIntelligenceFinding } from '../../types'

const SECTION_LABELS: Record<string, string> = {
  academic_orientation: 'Program character',
  theory_applied_balance: 'Theory and application',
  learning_experience: 'Learning experience',
  experiential_learning: 'Research and employer exposure',
  career_pathways: 'Career pathways',
  community_values: 'Community and values',
  who_thrives: 'Who thrives',
  challenges_tradeoffs: 'Challenges and tradeoffs',
  support_environment: 'Support environment',
  student_employer_evidence: 'Student and employer evidence',
}

const DEFAULT_ORDER = [
  'academic_orientation',
  'learning_experience',
  'experiential_learning',
  'career_pathways',
  'community_values',
  'who_thrives',
  'challenges_tradeoffs',
  'support_environment',
  'student_employer_evidence',
  'theory_applied_balance',
]

function sectionTitle(key: string) {
  return SECTION_LABELS[key] ?? key.replace(/_/g, ' ')
}

function sourceLabel(finding: ProfileIntelligenceFinding): string | null {
  if (finding.source_type === 'fact') return 'Sourced fact'
  if (finding.source_type === 'institution_confirmed') return 'Institution confirmed'
  // 'inferred' provenance + the numeric confidence are internal enrichment
  // signals — never surfaced to a reader as "Inferred from evidence · 76%".
  return null
}

interface ProfileIntelligenceSectionsProps {
  intelligence?: ProfileIntelligence | null
  compact?: boolean
}

export default function ProfileIntelligenceSections({
  intelligence,
  compact = false,
}: ProfileIntelligenceSectionsProps) {
  const sections = intelligence?.sections ?? {}
  const keys = [
    ...DEFAULT_ORDER.filter((key) => sections[key]?.findings?.length),
    ...Object.keys(sections).filter((key) => !DEFAULT_ORDER.includes(key) && sections[key]?.findings?.length),
  ]

  if (!intelligence || keys.length === 0) return null

  return (
    <section className={compact ? 'space-y-4' : 'space-y-6'} aria-label="Profile intelligence">
      {keys.map((key) => (
        <section key={key} className="border-t border-border pt-5 first:border-t-0 first:pt-0">
          <h3 className="text-sm font-semibold uppercase text-muted-foreground">
            {sectionTitle(key)}
          </h3>
          <div className="mt-3 space-y-4">
            {sections[key].findings.map((finding, index) => (
              <article key={`${key}-${index}`} className="space-y-2">
                <p className="text-sm leading-6 text-foreground">{finding.statement}</p>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  {sourceLabel(finding) && <span>{sourceLabel(finding)}</span>}
                  {finding.evidence.slice(0, 3).map((evidence) => (
                    <a
                      key={`${evidence.label}-${evidence.url}`}
                      className="underline underline-offset-2 hover:text-foreground"
                      href={evidence.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {evidence.label}
                    </a>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
      {Boolean(intelligence.omissions?.length) && (
        <section className="border-t border-border pt-5">
          <h3 className="text-sm font-semibold uppercase text-muted-foreground">
            Not yet published
          </h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
            {intelligence.omissions?.slice(0, 4).map((item) => (
              <li key={`${item.section}-${item.reason}`}>{item.reason}</li>
            ))}
          </ul>
        </section>
      )}
    </section>
  )
}
