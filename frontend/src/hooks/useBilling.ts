import { useQuery } from '@tanstack/react-query'

import { getStudentBilling } from '../api/billing'
import { useAuthStore } from '../stores/auth-store'

/** Student subscription state (Spec 07 §4.1). Fetched once and shared via the
 * 'student-billing' query key — banner, paywall, and Settings all read it. */
export function useStudentBilling() {
  const role = useAuthStore(s => s.user?.role)
  return useQuery({
    queryKey: ['student-billing'],
    queryFn: getStudentBilling,
    enabled: role === 'student',
    staleTime: 60_000,
  })
}
