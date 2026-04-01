import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getAIOpsSnapshot,
  getAIControlSLO,
  patchAIControlPolicy,
  runAIControlLoop,
  runAIEngineGraph,
  runDriftCheck,
  runMLCycle,
  triggerCrawlAll,
  triggerTraining,
} from '../api/admin'

export function useAdminOps() {
  const qc = useQueryClient()

  const snapshotQ = useQuery({
    queryKey: ['admin', 'ops', 'snapshot'],
    queryFn: getAIOpsSnapshot,
    refetchInterval: 8000,
  })

  const sloQ = useQuery({
    queryKey: ['admin', 'ops', 'slo'],
    queryFn: getAIControlSLO,
    refetchInterval: 8000,
  })

  const invalidateOps = async () => {
    await qc.invalidateQueries({ queryKey: ['admin', 'ops'] })
    await qc.invalidateQueries({ queryKey: ['admin', 'ai-control'] })
    await qc.invalidateQueries({ queryKey: ['admin', 'ml'] })
    await qc.invalidateQueries({ queryKey: ['admin', 'crawler'] })
  }

  const policyMut = useMutation({
    mutationFn: patchAIControlPolicy,
    onSuccess: invalidateOps,
  })

  const runLoopMut = useMutation({
    mutationFn: runAIControlLoop,
    onSuccess: invalidateOps,
  })

  const runEngineGraphMut = useMutation({
    mutationFn: runAIEngineGraph,
    onSuccess: invalidateOps,
  })

  const runCrawlAllMut = useMutation({
    mutationFn: triggerCrawlAll,
    onSuccess: invalidateOps,
  })

  const runMLCycleMut = useMutation({
    mutationFn: runMLCycle,
    onSuccess: invalidateOps,
  })

  const triggerTrainingMut = useMutation({
    mutationFn: triggerTraining,
    onSuccess: invalidateOps,
  })

  const driftCheckMut = useMutation({
    mutationFn: runDriftCheck,
    onSuccess: invalidateOps,
  })

  return {
    snapshotQ,
    sloQ,
    policyMut,
    runLoopMut,
    runEngineGraphMut,
    runCrawlAllMut,
    runMLCycleMut,
    triggerTrainingMut,
    driftCheckMut,
    invalidateOps,
  }
}
