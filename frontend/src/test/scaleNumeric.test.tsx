import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

import AnswerChoices from '../pages/student/discover/AnswerChoices'

describe('AnswerChoices scale — numeric mode (enrichment)', () => {
  it('numeric mode submits the slider NUMBER, not a phrase', () => {
    const onPick = vi.fn()
    render(<AnswerChoices kind="scale" options={[]} numeric onPick={onPick} />)
    fireEvent.change(screen.getByLabelText(/how important/i), { target: { value: '4' } })
    fireEvent.click(screen.getByRole('button', { name: /set/i }))
    // backend _coerce_weight_0_5 accepts a numeric string; the matcher needs a number, never a phrase
    expect(onPick).toHaveBeenCalledWith('4')
  })

  it('default (conversational) mode still submits the phrase', () => {
    const onPick = vi.fn()
    render(<AnswerChoices kind="scale" options={[]} onPick={onPick} />)
    fireEvent.click(screen.getByRole('button', { name: /set/i }))
    const arg = onPick.mock.calls[0][0] as string
    expect(arg).toMatch(/[a-z]/i) // a word/phrase, not a bare number
    expect(Number.isNaN(Number(arg))).toBe(true)
  })
})
