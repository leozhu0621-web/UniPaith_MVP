import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  bootstrapPrograms, refreshStudent, refreshProgram,
  verifyInstitution, getAdminActionAudit,
  getAIControlStatus, patchAIControlPolicy, runAIControlLoop, getAIControlAudit,
  getAIControlSLO, getAIEngineState, runAIEngineGraph,
} from '../../api/admin'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { useToastStore } from '../../stores/toast-store'
import {
  Cpu, RefreshCw, Building2, GraduationCap, User, CheckCircle,
} from 'lucide-react'

export default function AdminSystemPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [studentId, setStudentId] = useState('')
  const [programId, setProgramId] = useState('')
  const [institutionId, setInstitutionId] = useState('')
  const [policyBusy, setPolicyBusy] = useState(false)

  const controlQ = useQuery({
    queryKey: ['admin', 'ai-control', 'status'],
    queryFn: getAIControlStatus,
    refetchInterval: 10000,
  })
  const auditQ = useQuery({
    queryKey: ['admin', 'ai-control', 'audit'],
    queryFn: () => getAIControlAudit({ limit: 10 }),
    refetchInterval: 10000,
  })
  const engineStateQ = useQuery({
    queryKey: ['admin', 'ai-control', 'engine-state'],
    queryFn: getAIEngineState,
    refetchInterval: 10000,
  })
  const sloQ = useQuery({
    queryKey: ['admin', 'ai-control', 'slo'],
    queryFn: getAIControlSLO,
    refetchInterval: 10000,
  })
  const adminAuditQ = useQuery({
    queryKey: ['admin', 'audit', 'actions', 'system'],
    queryFn: () => getAdminActionAudit({ limit: 100 }),
    refetchInterval: 10000,
  })

  const bootstrapMut = useMutation({
    mutationFn: bootstrapPrograms,
    onSuccess: (data) => addToast(`Bootstrap complete: ${JSON.stringify(data)}`, 'success'),
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const refreshStudentMut = useMutation({
    mutationFn: refreshStudent,
    onSuccess: () => { addToast('Student features refreshed', 'success'); setStudentId('') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const refreshProgramMut = useMutation({
    mutationFn: refreshProgram,
    onSuccess: () => { addToast('Program features refreshed', 'success'); setProgramId('') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const verifyMut = useMutation({
    mutationFn: (institutionId: string) => verifyInstitution(institutionId),
    onSuccess: () => { addToast('Institution verified', 'success'); setInstitutionId('') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const runLoopMut = useMutation({
    mutationFn: runAIControlLoop,
    onSuccess: async () => {
      addToast('Self-driving loop tick triggered', 'success')
      await qc.invalidateQueries({ queryKey: ['admin', 'ai-control'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'ml'] })
      await qc.refetchQueries({ queryKey: ['admin', 'ai-control'], type: 'active' })
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const runEngineGraphMut = useMutation({
    mutationFn: runAIEngineGraph,
    onSuccess: async () => {
      addToast('Full AI engine graph run started/completed', 'success')
      await qc.invalidateQueries({ queryKey: ['admin', 'ai-control'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'ml'] })
      await qc.refetchQueries({ queryKey: ['admin', 'ai-control'], type: 'active' })
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const updatePolicy = async (data: {
    autonomy_enabled?: boolean
    auto_fix_enabled?: boolean
    emergency_stop?: boolean
  }) => {
    try {
      setPolicyBusy(true)
      await patchAIControlPolicy(data)
      addToast('AI policy updated', 'success')
      await qc.invalidateQueries({ queryKey: ['admin', 'ai-control'] })
    } catch (e: any) {
      addToast(e.message ?? 'Failed to update policy', 'error')
    } finally {
      setPolicyBusy(false)
    }
  }

  const policy = controlQ.data?.policy
  const llm = controlQ.data?.llm

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Tools</h1>
        <p className="text-sm text-gray-500">Administrative actions and system maintenance</p>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">AI Control Plane</h3>
            <p className="text-xs text-gray-500">Autonomy policy, OpenAI visibility, and self-driving loop controls</p>
          </div>
          <Button variant="secondary" onClick={() => controlQ.refetch()} disabled={controlQ.isFetching}>
            <RefreshCw size={14} className={`mr-2 ${controlQ.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">LLM Provider</p>
            <p className="text-sm font-semibold text-gray-900 mt-1">{llm?.provider ?? 'openai'}</p>
            <p className="text-xs text-gray-500 mt-1 break-all">{llm?.base_url ?? 'N/A'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Models</p>
            <p className="text-sm text-gray-900 mt-1">Feature: {llm?.feature_model ?? 'N/A'}</p>
            <p className="text-sm text-gray-900">Reasoning: {llm?.reasoning_model ?? 'N/A'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Loop Status</p>
            <p className="text-sm text-gray-900 mt-1">Last tick: {controlQ.data?.autonomy_loop?.last_tick_status ?? 'never_run'}</p>
            <p className="text-xs text-gray-500 mt-1">
              {controlQ.data?.autonomy_loop?.last_tick_at ?? 'No ticks yet'}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant={policy?.autonomy_enabled ? 'secondary' : 'primary'}
            disabled={policyBusy}
            onClick={() => updatePolicy({ autonomy_enabled: !policy?.autonomy_enabled })}
          >
            {policy?.autonomy_enabled ? 'Disable Autonomy' : 'Enable Autonomy'}
          </Button>
          <Button
            variant={policy?.auto_fix_enabled ? 'secondary' : 'primary'}
            disabled={policyBusy}
            onClick={() => updatePolicy({ auto_fix_enabled: !policy?.auto_fix_enabled })}
          >
            {policy?.auto_fix_enabled ? 'Disable Auto-Fix' : 'Enable Auto-Fix'}
          </Button>
          <Button
            variant={policy?.emergency_stop ? 'primary' : 'secondary'}
            disabled={policyBusy}
            onClick={() => updatePolicy({ emergency_stop: !policy?.emergency_stop })}
          >
            {policy?.emergency_stop ? 'Clear Emergency Stop' : 'Emergency Stop'}
          </Button>
          <Button onClick={() => runLoopMut.mutate()} disabled={runLoopMut.isPending}>
            {runLoopMut.isPending ? (
              <><RefreshCw size={14} className="mr-2 animate-spin" /> Running loop...</>
            ) : (
              <><Cpu size={14} className="mr-2" /> Run Self-Driving Tick</>
            )}
          </Button>
          <Button
            variant="secondary"
            onClick={() => runEngineGraphMut.mutate()}
            disabled={runEngineGraphMut.isPending}
          >
            {runEngineGraphMut.isPending ? (
              <><RefreshCw size={14} className="mr-2 animate-spin" /> Running full graph...</>
            ) : (
              <><Cpu size={14} className="mr-2" /> Run Full Engine Graph</>
            )}
          </Button>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">Autonomous Incidents & Audit</h3>
            <p className="text-xs text-gray-500">Recent detect/remediate/verify/rollback events</p>
          </div>
          <Button variant="secondary" onClick={() => auditQ.refetch()} disabled={auditQ.isFetching}>
            <RefreshCw size={14} className={`mr-2 ${auditQ.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 mb-3">
          <p className="text-xs text-gray-500">Engine Runtime</p>
          <p className="text-sm text-gray-900 mt-1">
            Status: {engineStateQ.data?.status ?? controlQ.data?.engine_runtime?.status ?? 'idle'}
          </p>
          <p className="text-xs text-gray-500">
            Last run started: {engineStateQ.data?.last_run_started_at ?? controlQ.data?.engine_runtime?.last_run_started_at ?? '—'}
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">LLM P95</p>
            <p className="text-sm font-semibold text-gray-900">{sloQ.data?.llm?.p95_ms ?? 0} ms</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Embedding P95</p>
            <p className="text-sm font-semibold text-gray-900">{sloQ.data?.embedding?.p95_ms ?? 0} ms</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Self-Driving Tick P95</p>
            <p className="text-sm font-semibold text-gray-900">{sloQ.data?.self_driving_tick?.p95_ms ?? 0} ms</p>
          </div>
        </div>
        <div className="space-y-2 max-h-80 overflow-auto">
          {(auditQ.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No incidents or audit events yet.</p>
          ) : (
            (auditQ.data?.items ?? []).slice().reverse().map((event: any, idx: number) => (
              <div key={`${event.timestamp}-${idx}`} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{event.event_type}</p>
                  <p className="text-xs text-gray-500">{event.timestamp}</p>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Status: {event.payload?.status ?? 'unknown'}
                </p>
              </div>
            ))
          )}
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">Admin Action History</h3>
            <p className="text-xs text-gray-500">Full feed of user and institution admin actions</p>
          </div>
          <Button
            variant="secondary"
            onClick={() => adminAuditQ.refetch()}
            disabled={adminAuditQ.isFetching}
          >
            <RefreshCw size={14} className={`mr-2 ${adminAuditQ.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <div className="space-y-2 max-h-96 overflow-auto">
          {(adminAuditQ.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No admin actions recorded yet.</p>
          ) : (
            (adminAuditQ.data?.items ?? []).map((event: any) => (
              <div key={event.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{event.action}</p>
                  <p className="text-xs text-gray-500">{event.created_at}</p>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {event.entity_type} · {event.entity_id}
                </p>
                {event.payload_json?.reason && (
                  <p className="text-xs text-gray-500 mt-1">Reason: {event.payload_json.reason}</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Bootstrap */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600"><Cpu size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">AI Bootstrap</h3>
              <p className="text-xs text-gray-500">Extract features & generate embeddings for all published programs</p>
            </div>
          </div>
          <Button onClick={() => bootstrapMut.mutate()} disabled={bootstrapMut.isPending} className="w-full">
            {bootstrapMut.isPending ? (
              <><RefreshCw size={14} className="mr-2 animate-spin" /> Running...</>
            ) : (
              <><Cpu size={14} className="mr-2" /> Bootstrap All Programs</>
            )}
          </Button>
        </Card>

        {/* Verify Institution */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-green-100 text-green-600"><Building2 size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Verify Institution</h3>
              <p className="text-xs text-gray-500">Mark an institution as verified</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input
              value={institutionId}
              onChange={e => setInstitutionId(e.target.value)}
              placeholder="Institution UUID"
              className="flex-1"
            />
            <Button onClick={() => verifyMut.mutate(institutionId)} disabled={verifyMut.isPending || !institutionId}>
              <CheckCircle size={14} className="mr-1" /> Verify
            </Button>
          </div>
        </Card>

        {/* Refresh Student */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600"><User size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Refresh Student Features</h3>
              <p className="text-xs text-gray-500">Re-extract AI features for a specific student</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input
              value={studentId}
              onChange={e => setStudentId(e.target.value)}
              placeholder="Student UUID"
              className="flex-1"
            />
            <Button onClick={() => refreshStudentMut.mutate(studentId)} disabled={refreshStudentMut.isPending || !studentId}>
              <RefreshCw size={14} className="mr-1" /> Refresh
            </Button>
          </div>
        </Card>

        {/* Refresh Program */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-purple-100 text-purple-600"><GraduationCap size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Refresh Program Features</h3>
              <p className="text-xs text-gray-500">Re-extract AI features for a specific program</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input
              value={programId}
              onChange={e => setProgramId(e.target.value)}
              placeholder="Program UUID"
              className="flex-1"
            />
            <Button onClick={() => refreshProgramMut.mutate(programId)} disabled={refreshProgramMut.isPending || !programId}>
              <RefreshCw size={14} className="mr-1" /> Refresh
            </Button>
          </div>
        </Card>
      </div>

      {/* System Info */}
      <Card className="p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Environment</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">API URL</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Frontend Build</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.MODE}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Node Env</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.PROD ? 'production' : 'development'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Version</p>
            <p className="text-sm font-mono text-gray-800 mt-1">MVP 0.1.0</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
