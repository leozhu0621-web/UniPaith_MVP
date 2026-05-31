import { useQuery } from '@tanstack/react-query'
import { getBilling } from '../api/billing'
import type { BillingStatus, Feature } from '../types/billing'

/** The student's resolved billing status (trial / free / plus, entitlements,
 * prices). Cached for a minute; refetched after billing mutations invalidate
 * the ['billing'] key. */
export function useBilling() {
  return useQuery<BillingStatus>({
    queryKey: ['billing'],
    queryFn: getBilling,
    staleTime: 60_000,
    retry: 1,
  })
}

export interface EntitlementResult {
  /** Whether the current plan may use the feature. Defaults to entitled while
   * loading and whenever billing is disabled, so paid UI never flashes locked. */
  entitled: boolean
  loading: boolean
  billing?: BillingStatus
}

/** Gate a paid feature in the UI. Mirrors the backend EntitlementService. */
export function useEntitlement(feature: Feature): EntitlementResult {
  const { data, isLoading } = useBilling()
  if (!data) return { entitled: true, loading: isLoading }
  if (!data.enabled) return { entitled: true, loading: false, billing: data }
  return {
    entitled: data.entitlements.includes(feature),
    loading: false,
    billing: data,
  }
}
