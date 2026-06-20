import { test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import AnswerChoices from '../pages/student/discover/AnswerChoices'

test('choice: tapping an option sends it immediately', () => {
  const onPick = vi.fn()
  render(<AnswerChoices kind="choice" options={["Master's", "Bachelor's"]} onPick={onPick} />)
  fireEvent.click(screen.getByText("Master's"))
  expect(onPick).toHaveBeenCalledWith("Master's")
})

test('multi: pick two then Continue sends the joined picks', () => {
  const onPick = vi.fn()
  render(<AnswerChoices kind="multi" options={['Funding', 'Community', 'Research']} onPick={onPick} />)
  fireEvent.click(screen.getByText('Funding'))
  fireEvent.click(screen.getByText('Community'))
  fireEvent.click(screen.getByRole('button', { name: /Continue/ }))
  expect(onPick).toHaveBeenCalledWith('Funding and Community')
})

test('scale: tap-meter sets the value and Set submits the raw number when numeric', () => {
  const onPick = vi.fn()
  render(<AnswerChoices kind="scale" options={[]} numeric onPick={onPick} />)
  // the meter is five tappable segments, not a slider
  fireEvent.click(screen.getByRole('button', { name: 'Set importance to 4' }))
  fireEvent.click(screen.getByRole('button', { name: 'Set' }))
  expect(onPick).toHaveBeenCalledWith('4')
})

test('multi asList: Continue sends an array instead of a joined string', () => {
  const onPick = vi.fn()
  render(
    <AnswerChoices
      kind="multi"
      options={['Funding', 'Community', 'Research']}
      onPick={onPick}
      asList
    />
  )
  fireEvent.click(screen.getByText('Funding'))
  fireEvent.click(screen.getByText('Community'))
  fireEvent.click(screen.getByRole('button', { name: /Continue/ }))
  expect(onPick).toHaveBeenCalledWith(['Funding', 'Community'])
})

test('multi without asList still sends the joined string (default unchanged)', () => {
  const onPick = vi.fn()
  render(
    <AnswerChoices
      kind="multi"
      options={['Alpha', 'Beta', 'Gamma']}
      onPick={onPick}
    />
  )
  fireEvent.click(screen.getByText('Alpha'))
  fireEvent.click(screen.getByText('Gamma'))
  fireEvent.click(screen.getByRole('button', { name: /Continue/ }))
  expect(onPick).toHaveBeenCalledWith('Alpha and Gamma')
})
