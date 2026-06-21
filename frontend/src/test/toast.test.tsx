import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import ToastContainer from '../components/ui/Toast'
import { useToastStore, type Toast } from '../stores/toast-store'

function setToasts(toasts: Toast[]) {
  act(() => {
    useToastStore.setState({ toasts })
  })
}

describe('ToastContainer', () => {
  beforeEach(() => {
    setToasts([])
  })

  afterEach(() => {
    setToasts([])
  })

  it('renders active notifications inside a named region', async () => {
    render(<ToastContainer />)
    setToasts([{ id: 'saved', message: 'Profile saved.', type: 'success' }])

    expect(await screen.findByRole('region', { name: 'Notifications' })).toBeInTheDocument()

    const toast = await screen.findByRole('status')
    expect(toast).toHaveAttribute('aria-live', 'polite')
    expect(toast).toHaveAttribute('aria-atomic', 'true')
    expect(toast).toHaveTextContent('Profile saved.')
    expect(screen.getByRole('button', { name: 'Dismiss notification' })).toBeInTheDocument()
  })

  it.each([
    ['error' as const, "We couldn't save your changes."],
    ['warning' as const, 'Review the missing deadline.'],
  ])('announces %s notifications assertively', async (type, message) => {
    render(<ToastContainer />)
    setToasts([{ id: type, message, type }])

    const toast = await screen.findByRole('alert')
    expect(toast).toHaveAttribute('aria-live', 'assertive')
    expect(toast).toHaveAttribute('aria-atomic', 'true')
    expect(toast).toHaveTextContent(message)
  })

  it('dismisses notifications with an accessible close action', async () => {
    render(<ToastContainer />)
    setToasts([{ id: 'manual', message: 'Check your upload.', type: 'info' }])

    fireEvent.click(await screen.findByRole('button', { name: 'Dismiss notification' }))

    expect(useToastStore.getState().toasts).toEqual([])
  })
})
