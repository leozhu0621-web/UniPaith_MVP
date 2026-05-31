// Spec 07 (Product Context §4) — public plan catalog (drives the pricing page).
import apiClient from './client'
import type { PlanCatalog } from '../types/billing'

export const getPlans = (): Promise<PlanCatalog> =>
  apiClient.get('/billing/plans').then(r => r.data)
