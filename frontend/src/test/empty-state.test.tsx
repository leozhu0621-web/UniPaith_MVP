import { fireEvent, render, screen } from '@testing-library/react'
import { Circle } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'

import EmptyState from '../components/ui/EmptyState'
import { COPY } from '../lib/copy'

describe('EmptyState', () => {
  it('uses shared empty copy and status semantics by default', () => {
    render(<EmptyState />)

    expect(screen.getByRole('status')).toHaveTextContent(COPY.emptyGeneric)
  })

  it('keeps icons decorative and exposes the action by label', () => {
    const onClick = vi.fn()
    render(
      <EmptyState
        icon={<Circle data-testid="empty-state-icon" />}
        title="No campaigns yet"
        description="Create one when outreach is ready."
        action={{ label: 'Create campaign', onClick }}
      />
    )

    expect(screen.getByRole('status')).toHaveTextContent('No campaigns yet')
    expect(screen.getByRole('status')).toHaveTextContent('Create one when outreach is ready.')
    expect(screen.getByTestId('empty-state-icon').closest('[aria-hidden="true"]')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Create campaign' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })
})
