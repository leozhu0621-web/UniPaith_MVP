// Spec 54 §4 — the one optimistic-mutation shape, factored into a hook.
//
// Every save / react / RSVP / stage-move / mark-read on the product applies
// instantly and reconciles against the server (the §53 experience bar). Hand-
// rolling the cancel → snapshot → patch → rollback → invalidate dance per call
// site drifts; this helper makes every surface use it identically.
//
// Lifecycle (exactly the spec §4 reference):
//   onMutate   cancel in-flight queries, snapshot the cache, apply the patch
//   onError    roll the cache back to the snapshot
//   onSettled  invalidate to re-sync with the server (the patched key + extras)

import {
  useMutation,
  useQueryClient,
  type QueryKey,
  type UseMutationResult,
} from '@tanstack/react-query'

export interface OptimisticMutationConfig<TData, TVariables, TSnapshot> {
  /** The async write. */
  mutationFn: (vars: TVariables) => Promise<TData>
  /** The cache key to patch optimistically (static, or derived from vars). */
  queryKey: QueryKey | ((vars: TVariables) => QueryKey)
  /** Produce the next cached value from the current one + the variables. */
  optimisticUpdate: (current: TSnapshot | undefined, vars: TVariables) => TSnapshot
  /** Extra keys to invalidate on settle (the patched key is always included). */
  invalidateKeys?: QueryKey[] | ((vars: TVariables) => QueryKey[])
  onError?: (error: unknown, vars: TVariables) => void
  onSuccess?: (data: TData, vars: TVariables) => void
}

interface RollbackContext<TSnapshot> {
  key: QueryKey
  previous: TSnapshot | undefined
}

export function useOptimisticMutation<TData, TVariables, TSnapshot>(
  config: OptimisticMutationConfig<TData, TVariables, TSnapshot>,
): UseMutationResult<TData, unknown, TVariables, RollbackContext<TSnapshot>> {
  const qc = useQueryClient()

  return useMutation<TData, unknown, TVariables, RollbackContext<TSnapshot>>({
    mutationFn: config.mutationFn,
    onMutate: async (vars) => {
      const key = typeof config.queryKey === 'function' ? config.queryKey(vars) : config.queryKey
      // Stop in-flight refetches so they don't clobber the optimistic value.
      await qc.cancelQueries({ queryKey: key })
      const previous = qc.getQueryData<TSnapshot>(key)
      qc.setQueryData<TSnapshot>(key, (current) => config.optimisticUpdate(current, vars))
      return { key, previous }
    },
    onError: (error, vars, ctx) => {
      // Roll back to exactly what was there before the optimistic write.
      if (ctx) qc.setQueryData(ctx.key, ctx.previous)
      config.onError?.(error, vars)
    },
    onSuccess: (data, vars) => {
      config.onSuccess?.(data, vars)
    },
    onSettled: (_data, _error, vars, ctx) => {
      const keys: QueryKey[] = ctx ? [ctx.key] : []
      const extra =
        typeof config.invalidateKeys === 'function'
          ? config.invalidateKeys(vars)
          : config.invalidateKeys
      if (extra) keys.push(...extra)
      for (const key of keys) {
        void qc.invalidateQueries({ queryKey: key })
      }
    },
  })
}
