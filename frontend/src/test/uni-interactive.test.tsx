import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import AnswerChoices from '../pages/student/discover/AnswerChoices'
import NoticedCard from '../pages/student/discover/NoticedCard'
import type { NoticedItem } from '../pages/student/discover/noticed'

describe('Uni interactive UX — Phase 1', () => {
  it('AnswerChoices renders suggested options as tap-to-answer cards and sends on tap', () => {
    const onPick = vi.fn()
    render(<AnswerChoices options={['Doing meaningful work', 'Financial security']} onPick={onPick} />)
    fireEvent.click(screen.getByRole('button', { name: /doing meaningful work/i }))
    expect(onPick).toHaveBeenCalledWith('Doing meaningful work')
  })

  it('AnswerChoices renders nothing when there are no options', () => {
    const { container } = render(<AnswerChoices options={[]} onPick={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('AnswerChoices disables the cards while a turn is in flight', () => {
    render(<AnswerChoices options={['One', 'Two']} onPick={() => {}} disabled />)
    expect(screen.getByRole('button', { name: /^one$/i })).toBeDisabled()
  })

  it('NoticedCard shows a +N count and the noticed labels', () => {
    const items = [
      { label: 'wants meaningful work' },
      { label: 'funding matters' },
    ] as NoticedItem[]
    render(<NoticedCard items={items} />)
    expect(screen.getByText('+2')).toBeInTheDocument()
    expect(screen.getByText('wants meaningful work')).toBeInTheDocument()
    expect(screen.getByText('funding matters')).toBeInTheDocument()
  })

  it('NoticedCard renders nothing when there is nothing to reflect back', () => {
    const { container } = render(<NoticedCard items={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('AnswerChoices multi-select sends the joined picks on Continue', () => {
    const onPick = vi.fn()
    render(<AnswerChoices kind="multi" options={['Research', 'Teaching', 'Industry']} onPick={onPick} />)
    fireEvent.click(screen.getByRole('button', { name: /research/i }))
    fireEvent.click(screen.getByRole('button', { name: /industry/i }))
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    expect(onPick).toHaveBeenCalledWith('Research and Industry')
  })

  it('AnswerChoices scale renders a tap-meter and sends an importance phrase', () => {
    const onPick = vi.fn()
    render(
      <AnswerChoices
        kind="scale"
        options={['nice to have', 'must have']}
        onPick={onPick}
        lowLabel="nice to have"
        highLabel="must have"
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Set importance to 5' }))
    fireEvent.click(screen.getByRole('button', { name: /^set$/i }))
    expect(onPick).toHaveBeenCalledWith('must have')
  })
})
