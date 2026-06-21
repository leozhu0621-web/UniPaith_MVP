import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import IntegrationsCard from '../pages/institution/settings/IntegrationsCard'

describe('IntegrationsCard release state', () => {
  it('shows current connector status without product-visible placeholder copy', () => {
    render(
      <MemoryRouter>
        <IntegrationsCard primaryDomain="foo.edu" />
      </MemoryRouter>,
    )

    expect(screen.getByText('Email sending domain')).toBeInTheDocument()
    expect(screen.getByText(/use csv upload and exports/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open data upload/i })).toHaveAttribute('href', '/i/data')
    expect(screen.getAllByText('Not connected')).toHaveLength(4)
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument()
  })
})
