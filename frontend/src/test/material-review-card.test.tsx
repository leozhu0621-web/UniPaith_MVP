import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import MaterialReviewCard from '../components/student/MaterialReviewCard'
import type { ProposedProfile } from '../api/materials'

const proposed: ProposedProfile = {
  summary: 'I picked up your CS degree and a goal.',
  academic_records: [{ institution_name: 'State University', degree_type: 'bachelors' }],
  goals: [{ category: 'academic', specific: 'Earn a funded CS PhD' }],
}

describe('MaterialReviewCard', () => {
  it('shows what Uni found and confirms the kept sections', () => {
    const onConfirm = vi.fn()
    render(<MaterialReviewCard proposed={proposed} onConfirm={onConfirm} onCancel={() => {}} />)
    expect(screen.getByText(/here's what i found/i)).toBeInTheDocument()
    expect(screen.getByText('Education')).toBeInTheDocument()
    expect(screen.getByText('Goals')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /add to my space/i }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
    const sel = onConfirm.mock.calls[0][0]
    expect(sel.academic_records).toHaveLength(1)
    expect(sel.goals).toHaveLength(1)
  })

  it('drops a section the student unchecks', () => {
    const onConfirm = vi.fn()
    render(<MaterialReviewCard proposed={proposed} onConfirm={onConfirm} onCancel={() => {}} />)
    // Toggle "Goals" off.
    fireEvent.click(screen.getByRole('button', { name: /goals/i }))
    fireEvent.click(screen.getByRole('button', { name: /add to my space/i }))
    const sel = onConfirm.mock.calls[0][0]
    expect(sel.goals).toBeUndefined()
    expect(sel.academic_records).toHaveLength(1)
  })

  it('renders a graceful note when nothing was extracted', () => {
    const onCancel = vi.fn()
    render(<MaterialReviewCard proposed={{ summary: 'x' }} onConfirm={() => {}} onCancel={onCancel} />)
    expect(screen.getByText(/couldn't pull anything structured/i)).toBeInTheDocument()
  })
})
