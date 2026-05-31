/**
 * Spec 17 — Inbox unit tests (presentational + helpers).
 *
 * Covers the §12 checklist testable without a live backend: action labels
 * render as chips; the AI suggested reply renders, is editable, and sends;
 * empty state copy; thread eyebrow + waiting/ due helpers.
 */
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import SuggestedReplyCard from '../pages/student/inbox/SuggestedReplyCard'
import InboxList from '../pages/student/inbox/InboxList'
import { formatDue, threadEyebrow, waitingCopy } from '../pages/student/inbox/actionLabels'
import type { InboxThreadSummary } from '../types'

function makeThread(p: Partial<InboxThreadSummary> = {}): InboxThreadSummary {
  return {
    id: p.id || 'T1',
    application_id: p.application_id ?? 'A1',
    application: p.application || { program_name: 'CS MS', institution_name: 'University of Foo' },
    type: p.type || 'human',
    subject: p.subject ?? 'Second recommender',
    action_label: p.action_label ?? 'needs_reply',
    due_date: p.due_date ?? null,
    waiting_on: p.waiting_on ?? 'student',
    unread: p.unread ?? true,
    last_message_at: p.last_message_at ?? new Date().toISOString(),
    linked_checklist_item_category: p.linked_checklist_item_category ?? null,
    linked_calendar_item_id: p.linked_calendar_item_id ?? null,
  }
}

describe('inbox helpers', () => {
  it('builds the thread eyebrow from institution + program', () => {
    expect(threadEyebrow(makeThread())).toBe('University of Foo · CS MS')
    expect(threadEyebrow(makeThread({ application: { program_name: null, institution_name: 'U Foo' } }))).toBe('U Foo')
    expect(threadEyebrow(makeThread({ type: 'system', application: { program_name: null, institution_name: null } }))).toBe('UniPaith')
  })

  it('describes who is waiting', () => {
    expect(waitingCopy(makeThread({ waiting_on: 'student' }))).toBe('Waiting on you')
    expect(waitingCopy(makeThread({ waiting_on: 'school' }))).toBe('Waiting on University of Foo')
    expect(waitingCopy(makeThread({ waiting_on: 'none' }))).toBeNull()
  })

  it('formats a due date or returns null', () => {
    expect(formatDue(null)).toBeNull()
    expect(formatDue('2026-12-10T00:00:00Z')).toMatch(/Dec/)
  })
})

describe('SuggestedReplyCard (§7)', () => {
  const reply = {
    draft: 'Thanks for the heads up — sending now.',
    tone: 'professional',
    length: 'medium',
    alternate_drafts: ['Shorter version.', 'Warmer version.'],
  }

  it('renders the AI suggestion badge and the editable draft', () => {
    render(<SuggestedReplyCard reply={reply} sending={false} onSend={() => {}} />)
    expect(screen.getByText('AI suggestion')).toBeInTheDocument()
    const ta = screen.getByLabelText('Suggested reply draft') as HTMLTextAreaElement
    expect(ta.value).toBe('Thanks for the heads up — sending now.')
  })

  it('sends the edited text (never auto-sends)', () => {
    const onSend = vi.fn()
    render(<SuggestedReplyCard reply={reply} sending={false} onSend={onSend} />)
    const ta = screen.getByLabelText('Suggested reply draft')
    fireEvent.change(ta, { target: { value: 'My edited reply' } })
    fireEvent.click(screen.getByRole('button', { name: /edit & send/i }))
    expect(onSend).toHaveBeenCalledWith('My edited reply')
  })

  it('swaps in an alternate-tone draft', () => {
    render(<SuggestedReplyCard reply={reply} sending={false} onSend={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: 'Alt 1' }))
    const ta = screen.getByLabelText('Suggested reply draft') as HTMLTextAreaElement
    expect(ta.value).toBe('Shorter version.')
  })
})

describe('InboxList', () => {
  const filters = { type: 'all' as const, state: 'all' as const, application_id: 'all', sort: 'urgent' as const }

  it('renders action-label chips for each thread', () => {
    render(
      <InboxList
        threads={[
          makeThread({ id: 'T1', action_label: 'needs_reply', subject: 'Reply please' }),
          makeThread({ id: 'T2', action_label: 'completed', subject: 'All set', waiting_on: 'none' }),
        ]}
        loading={false}
        selectedId={null}
        onSelect={() => {}}
        filters={filters}
        onFilters={() => {}}
        appOptions={[{ value: 'all', label: 'All applications' }]}
      />,
    )
    // Each label appears once in the filter <select> option and once as the
    // row chip — 2 occurrences confirms the chip rendered beyond the option.
    expect(screen.getAllByText('Needs reply').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Completed').length).toBeGreaterThanOrEqual(2)
  })

  it('shows the empty-state copy when there are no threads', () => {
    render(
      <InboxList
        threads={[]}
        loading={false}
        selectedId={null}
        onSelect={() => {}}
        filters={filters}
        onFilters={() => {}}
        appOptions={[{ value: 'all', label: 'All applications' }]}
      />,
    )
    expect(screen.getByText(/No conversations yet/i)).toBeInTheDocument()
  })

  it('fires onSelect when a thread row is clicked', () => {
    const onSelect = vi.fn()
    render(
      <InboxList
        threads={[makeThread({ id: 'T9', subject: 'Open me' })]}
        loading={false}
        selectedId={null}
        onSelect={onSelect}
        filters={filters}
        onFilters={() => {}}
        appOptions={[{ value: 'all', label: 'All applications' }]}
      />,
    )
    fireEvent.click(screen.getByText('Open me'))
    expect(onSelect).toHaveBeenCalledWith('T9')
  })
})
