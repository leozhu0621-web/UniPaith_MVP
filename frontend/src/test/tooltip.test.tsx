import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import AIBadge from '../components/ui/AIBadge'
import Tooltip from '../components/ui/Tooltip'

describe('Tooltip', () => {
  it('connects the trigger to tooltip content for assistive tech', () => {
    render(
      <Tooltip content="Confidence is based on profile depth.">
        <span>High confidence</span>
      </Tooltip>,
    )

    const tooltip = screen.getByRole('tooltip')
    const trigger = screen.getByText('High confidence').closest('[aria-describedby]')

    expect(trigger).toHaveAttribute('tabindex', '0')
    expect(trigger).toHaveAttribute('aria-describedby', tooltip.id)
    expect(tooltip).toHaveTextContent('Confidence is based on profile depth.')
  })

  it('does not add tooltip semantics when disabled', () => {
    render(
      <Tooltip content="Hidden copy" disabled>
        <span>Plain label</span>
      </Tooltip>,
    )

    expect(screen.queryByRole('tooltip')).toBeNull()
    expect(screen.getByText('Plain label').closest('[aria-describedby]')).toBeNull()
  })
})

describe('AIBadge', () => {
  it('exposes AI provenance through the shared tooltip', () => {
    render(<AIBadge label="AI packet summary" />)

    expect(screen.getByText('AI packet summary').closest('[aria-describedby]')).toBeTruthy()
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      'AI helped prepare this content. Review important details before acting.',
    )
  })

  it('explains rule-based fallback without hiding the badge state', () => {
    render(<AIBadge fallback />)

    expect(screen.getByText('Rule-based')).toBeInTheDocument()
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      'Shown from the rule-based fallback because the AI path was unavailable.',
    )
  })
})
