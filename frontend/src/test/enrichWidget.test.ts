import { describe, expect, it } from 'vitest'

import { humanizeField } from '../components/student/enrichHelpers'

describe('humanizeField', () => {
  it('title-cases plain field keys', () => {
    expect(humanizeField('weight_cost')).toBe('Weight Cost')
    expect(humanizeField('preferred_countries')).toBe('Preferred Countries')
  })

  it('uses special-cased labels', () => {
    expect(humanizeField('gpa')).toBe('GPA')
    expect(humanizeField('date_of_birth')).toBe('Date of birth')
    expect(humanizeField('field_of_interest')).toBe('Field of interest')
  })
})
