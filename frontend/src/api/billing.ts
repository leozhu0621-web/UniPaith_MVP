import apiClient from './client'
import type {
  AddPaymentMethodInput,
  BillingEvent,
  BillingStatus,
  InstitutionUsage,
} from '../types/billing'

// Student billing (Spec 06 §4) ----------------------------------------------

export const getBilling = (): Promise<BillingStatus> =>
  apiClient.get('/students/me/billing').then(r => r.data)

export const addPaymentMethod = (data: AddPaymentMethodInput) =>
  apiClient.post('/students/me/billing/payment-method', data).then(r => r.data)

export const subscribe = (): Promise<BillingStatus> =>
  apiClient.post('/students/me/billing/subscribe').then(r => r.data)

export const setAdFree = (enabled: boolean): Promise<BillingStatus> =>
  apiClient.post('/students/me/billing/ad-free', { enabled }).then(r => r.data)

export const cancelSubscription = (): Promise<BillingStatus> =>
  apiClient.post('/students/me/billing/cancel').then(r => r.data)

export const getBillingHistory = (): Promise<BillingEvent[]> =>
  apiClient.get('/students/me/billing/history').then(r => r.data)

// Institution billing --------------------------------------------------------

export const getInstitutionUsage = (): Promise<InstitutionUsage> =>
  apiClient.get('/institutions/me/billing/usage').then(r => r.data)
