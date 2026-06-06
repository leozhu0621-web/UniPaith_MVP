/**
 * Regression — Modal must not steal focus when its parent re-renders.
 *
 * Bug: the focus-management effect listed `onClose` in its dependency array.
 * Callers pass an inline arrow (`onClose={() => setOpen(false)}`) that gets a
 * new identity on every render, so every keystroke (which re-renders the parent
 * that owns the form state, e.g. FeedbackWidget) re-ran the effect and forced
 * focus back to the FIRST field. Net effect: you could only type one character
 * in any non-first field before focus jumped away. This test reproduces that
 * exact scenario with the real Modal + a changing onClose.
 */
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Modal from '../components/ui/Modal'

function Harness() {
  // `onClose` is a fresh arrow each render — exactly what real callers pass.
  // The button forces a parent re-render, standing in for the setState that a
  // keystroke triggers in a form-owning component.
  const [, force] = useState(0)
  return (
    <Modal isOpen onClose={() => {}} title="Send feedback">
      <input data-testid="title" />
      <textarea data-testid="message" />
      <button onClick={() => force(n => n + 1)}>force-rerender</button>
    </Modal>
  )
}

describe('Modal focus stability', () => {
  it('keeps caret in the focused field across a parent re-render', () => {
    render(<Harness />)

    // Move focus to the SECOND field (the message box), as a user would.
    const message = screen.getByTestId('message') as HTMLTextAreaElement
    message.focus()
    expect(document.activeElement).toBe(message)

    // A keystroke re-renders the parent → Modal receives a new onClose identity.
    fireEvent.click(screen.getByText('force-rerender'))

    // Focus MUST stay on the message field. With the bug it jumps to `title`.
    expect(document.activeElement).toBe(message)
  })
})
