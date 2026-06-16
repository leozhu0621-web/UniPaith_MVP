import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import StudentTitle from '../components/layout/StudentTitle'

describe('Discover → Chat rename', () => {
  it('sets the /s browser tab title to "Chat"', () => {
    render(
      <MemoryRouter initialEntries={['/s']}>
        <StudentTitle />
      </MemoryRouter>,
    )
    expect(document.title).toBe('Chat · UniPaith')
  })

  it('does not title the surface "Discover"', () => {
    render(
      <MemoryRouter initialEntries={['/s']}>
        <StudentTitle />
      </MemoryRouter>,
    )
    expect(document.title).not.toMatch(/Discover/)
  })
})
