import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import FollowUpCard from '../components/student/FollowUpCard'
import type { FollowupQuestion } from '../api/materials'

const qs: FollowupQuestion[] = [
  { id: 'g1', category: 'missing', target_field: 'gpa', kind: 'text', prompt: "What's your GPA?" },
  { id: 'g2', category: 'ambiguous', target_field: 'activity_role', kind: 'choice', prompt: 'Role?', options: ['Member', 'President'] },
]

describe('FollowUpCard', () => {
  it('shows the first question and answers via text', async () => {
    const onAnswer = vi.fn().mockResolvedValue(undefined)
    render(<FollowUpCard questions={qs} onAnswer={onAnswer} onDone={() => {}} />)
    expect(screen.getByText(/what's your gpa/i)).toBeInTheDocument()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '3.8' } })
    fireEvent.click(screen.getByRole('button', { name: /^add$/i }))
    expect(onAnswer).toHaveBeenCalledWith(qs[0], '3.8')
  })

  it('answers a choice question by tapping a chip', () => {
    const onAnswer = vi.fn().mockResolvedValue(undefined)
    render(<FollowUpCard questions={[qs[1]]} onAnswer={onAnswer} onDone={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: /president/i }))
    expect(onAnswer).toHaveBeenCalledWith(qs[1], 'President')
  })

  it('calls onDone when skipping the last question', () => {
    const onDone = vi.fn()
    render(<FollowUpCard questions={[qs[0]]} onAnswer={() => {}} onDone={onDone} />)
    fireEvent.click(screen.getByRole('button', { name: /done/i }))
    expect(onDone).toHaveBeenCalled()
  })
})
