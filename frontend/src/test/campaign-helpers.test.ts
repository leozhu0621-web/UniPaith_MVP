import { describe, it, expect } from 'vitest'
import { parseContactsText, STATUS_BADGE, OBJECTIVE_LABELS } from '../pages/institution/campaigns/constants'

describe('Spec 25 — campaign helpers', () => {
  it('parses a CSV with header into contact rows', () => {
    const rows = parseContactsText('email,first_name,last_name\nana@x.com,Ana,Lee\nben@x.com,Ben,Ng')
    expect(rows).toHaveLength(2)
    expect(rows[0]).toMatchObject({ email: 'ana@x.com', first_name: 'Ana', last_name: 'Lee' })
  })

  it('parses a bare newline list of emails', () => {
    const rows = parseContactsText('ana@x.com\nben@x.com\nnot-an-email\ncara@x.com')
    expect(rows.map((r) => r.email)).toEqual(['ana@x.com', 'ben@x.com', 'cara@x.com'])
  })

  it('skips rows without a valid email', () => {
    const rows = parseContactsText('email\n\nfoo\nvalid@x.com')
    expect(rows).toHaveLength(1)
    expect(rows[0].email).toBe('valid@x.com')
  })

  it('maps lifecycle statuses to brand badge variants (active=success, scheduled=info)', () => {
    expect(STATUS_BADGE.active).toBe('success')
    expect(STATUS_BADGE.scheduled).toBe('info')
    expect(STATUS_BADGE.pending_approval).toBe('warning')
    expect(STATUS_BADGE.draft).toBe('neutral')
  })

  it('has a human label for every objective', () => {
    expect(OBJECTIVE_LABELS.event_promotion).toBe('Event promotion')
    expect(OBJECTIVE_LABELS.application_open).toBe('Application open')
  })
})
