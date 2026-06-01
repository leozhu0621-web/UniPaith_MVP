/**
 * Spec 39 · Fees & Payments — frontend smoke.
 *
 * Guards the submit-gate mirror logic (isFeeClear must match the backend's
 * services/payments/config.is_fee_clear) and the brand rule that checkout uses
 * the cobalt CTA, never the gold primary (Spec 39 §8).
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { isFeeClear, formatMoney, type FeeView, type CheckoutSession } from '../api/payments'
import PaymentCheckout from '../components/student/PaymentCheckout'

const feeBase: FeeView = {
  kind: 'application_fee',
  required: true,
  status: 'due',
  amount: 75,
  amount_cents: 7500,
  currency: 'USD',
  waiver_policy: 'allow_and_reconcile',
  auto_rules: [],
  waiver: null,
  paid_at: null,
  refunded_amount: null,
  payment_id: null,
}

describe('isFeeClear — submit gate (Spec 39 §2.2/§7)', () => {
  it('clears when no fee is required', () => {
    expect(isFeeClear(null)).toBe(true)
    expect(isFeeClear(undefined)).toBe(true)
    expect(isFeeClear({ ...feeBase, required: false })).toBe(true)
  })

  it('blocks a fee that is still due', () => {
    expect(isFeeClear(feeBase)).toBe(false)
  })

  it('clears once paid or waived', () => {
    expect(isFeeClear({ ...feeBase, status: 'paid' })).toBe(true)
    expect(isFeeClear({ ...feeBase, status: 'waived' })).toBe(true)
  })

  it('allow-and-reconcile lets a pending waiver through; block-until-approved does not', () => {
    expect(isFeeClear({ ...feeBase, status: 'waiver_pending' })).toBe(true)
    expect(
      isFeeClear({ ...feeBase, status: 'waiver_pending', waiver_policy: 'block_until_approved' }),
    ).toBe(false)
  })
})

describe('formatMoney', () => {
  it('renders an explicit amount', () => {
    expect(formatMoney(75, 'USD')).toContain('75')
  })
})

describe('PaymentCheckout (Spec 39 §8 — calm, cobalt, never gold)', () => {
  const session: CheckoutSession = {
    payment_id: 'p1',
    provider: 'mock',
    inline: true,
    checkout_url: null,
    publishable_key: null,
    amount: 75,
    amount_cents: 7500,
    currency: 'USD',
    kind: 'application_fee',
    status: 'pending',
  }

  it('shows the amount, a test-mode note, and a cobalt (not gold) pay button', () => {
    render(<PaymentCheckout session={session} onClose={() => {}} onPaid={() => {}} />)
    expect(screen.getByText(/Amount due/i)).toBeInTheDocument()
    expect(screen.getAllByText(/\$75/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Test mode/i)).toBeInTheDocument()

    const payBtn = screen.getByRole('button', { name: /Pay \$75/i })
    expect(payBtn.className).toContain('bg-secondary') // cobalt workhorse
    expect(payBtn.className).not.toContain('bg-primary') // never the gold accent
  })

  it('renders nothing without a session', () => {
    const { container } = render(
      <PaymentCheckout session={null} onClose={() => {}} onPaid={() => {}} />,
    )
    expect(container.firstChild).toBeNull()
  })
})
