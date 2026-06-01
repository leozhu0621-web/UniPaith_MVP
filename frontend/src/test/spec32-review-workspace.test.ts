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
})
