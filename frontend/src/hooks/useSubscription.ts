// Spec 07 (Product Context §4) — subscription / entitlement hooks.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  cancelSubscription,
  resumeSubscription,
  setAdFree,
  subscribe,
  getSubscription,
} from '../api/subscription'
import { getPlans } from '../api/billing'
import { useAuthStore } from '../stores/auth-store'
import { showToast } from '../stores/toast-store'
import type { SubscribePayload, Subscription } from '../types/billing'

const SUB_KEY = ['subscription']
const PLANS_KEY = ['billing-plans']

/** Current student's subscription. Only fetched for authenticated students. */
export function useSubscription() {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated)
  const role = useAuthStore(s => s.user?.role)
  return useQuery<Subscription>({
    queryKey: SUB_KEY,
    queryFn: getSubscription,
    enabled: isAuthenticated && role === 'student',
    staleTime: 60_000,
  })
}

/** Public plan catalog for the pricing page. */
export function usePlans() {
  return useQuery({ queryKey: PLANS_KEY, queryFn: getPlans, staleTime: 10 * 60_000 })
}

/**
 * Soft feature gate. Returns `entitled` for a pro feature key. While the
 * subscription is still loading we report `entitled: true` so the core journey
 * never flashes a paywall — gating only kicks in once status is known.
 */
export function useEntitlement(feature: string) {
  const { data, isLoading } = useSubscription()
  return {
    entitled: data ? data.entitlements.includes(feature) : true,
    loading: isLoading,
    subscription: data,
  }
}

export function useSubscribe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SubscribePayload) => subscribe(payload),
    onSuccess: data => {
      qc.setQueryData(SUB_KEY, data)
      showToast('You are now on UniPaith Pro', 'success')
    },
    onError: (e: Error) => showToast(e.message || 'Could not complete checkout', 'error'),
  })
}

export function useCancelSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: cancelSubscription,
    onSuccess: data => {
      qc.setQueryData(SUB_KEY, data)
      showToast('Your subscription will not renew', 'success')
    },
    onError: (e: Error) => showToast(e.message || 'Could not cancel', 'error'),
  })
}

export function useResumeSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: resumeSubscription,
    onSuccess: data => {
      qc.setQueryData(SUB_KEY, data)
      showToast('Welcome back to UniPaith Pro', 'success')
    },
    onError: (e: Error) => showToast(e.message || 'Could not resume', 'error'),
  })
}

export function useToggleAdFree() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (enabled: boolean) => setAdFree(enabled),
    onSuccess: data => {
      qc.setQueryData(SUB_KEY, data)
      showToast(data.ad_free ? 'Ad-free is on' : 'Ad-free is off', 'success')
    },
    onError: (e: Error) => showToast(e.message || 'Could not update', 'error'),
  })
}
