import { describe, expect, it } from 'vitest'
import { admissionsUrl, applicantUrl } from '../utils/institution-routes'

/** Spec 32 — review workspace route contract. */
describe('Spec 32 review workspace routes', () => {
  it('builds applicant review URLs under admissions intake', () => {
    expect(applicantUrl('app-123')).toBe('/i/admissions/applicant/app-123')
    expect(applicantUrl('app-123', 'scores')).toBe('/i/admissions/applicant/app-123?tab=scores')
  })

  it('embeds cohort compare in admissions tab IA', () => {
    expect(admissionsUrl('cohort')).toBe('/i/admissions?tab=cohort')
  })

  it('pre-filters the integrity queue to one signal type (dashboard chip)', () => {
    expect(admissionsUrl('integrity', undefined, 'duplicate_submission')).toBe(
      '/i/admissions?tab=integrity&type=duplicate_submission'
    )
    // No type → the plain queue URL is unchanged.
    expect(admissionsUrl('integrity')).toBe('/i/admissions?tab=integrity')
  })
})
