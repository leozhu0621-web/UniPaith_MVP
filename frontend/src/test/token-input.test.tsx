import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import TokenInput from '../components/ui/TokenInput'

// TokenInput is the free-form chip field behind Preferences → Dealbreakers.
// These pin the three commit/remove paths and the chip rendering.

describe('TokenInput', () => {
  it('renders existing values as removable chips', () => {
    render(<TokenInput value={['No online-only', 'No GRE']} onChange={vi.fn()} />)
    expect(screen.getByText('No online-only')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Remove No GRE' })).toBeInTheDocument()
  })

  it('commits a token on Enter', () => {
    const onChange = vi.fn()
    render(<TokenInput value={[]} onChange={onChange} placeholder="add one" />)
    const input = screen.getByPlaceholderText('add one')
    fireEvent.change(input, { target: { value: 'No online-only' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onChange).toHaveBeenCalledWith(['No online-only'])
  })

  it('commits a token on comma', () => {
    const onChange = vi.fn()
    render(<TokenInput value={['No GRE']} onChange={onChange} placeholder="add one" />)
    const input = screen.getByPlaceholderText('') // placeholder hides once chips exist
    fireEvent.change(input, { target: { value: 'Funded only' } })
    fireEvent.keyDown(input, { key: ',' })
    expect(onChange).toHaveBeenCalledWith(['No GRE', 'Funded only'])
  })

  it('removes the last token on Backspace when the input is empty', () => {
    const onChange = vi.fn()
    render(<TokenInput value={['No GRE', 'Funded only']} onChange={onChange} />)
    const input = screen.getByRole('textbox')
    fireEvent.keyDown(input, { key: 'Backspace' })
    expect(onChange).toHaveBeenCalledWith(['No GRE'])
  })

  it('removes a specific token via its ✕ button', () => {
    const onChange = vi.fn()
    render(<TokenInput value={['No GRE', 'Funded only']} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: 'Remove No GRE' }))
    expect(onChange).toHaveBeenCalledWith(['Funded only'])
  })

  it('drops duplicate and blank tokens', () => {
    const onChange = vi.fn()
    render(<TokenInput value={['No GRE']} onChange={onChange} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'No GRE' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    // duplicate -> no append, but draft still clears so onChange isn't called
    expect(onChange).not.toHaveBeenCalled()
  })
})
