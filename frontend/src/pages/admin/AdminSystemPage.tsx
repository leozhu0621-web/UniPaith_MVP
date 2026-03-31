import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  bootstrapPrograms, refreshStudent, refreshProgram,
  verifyInstitution,
} from '../../api/admin'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { useToastStore } from '../../stores/toast-store'
import {
  Cpu, RefreshCw, Building2, GraduationCap, User, CheckCircle,
} from 'lucide-react'

export default function AdminSystemPage() {
  const addToast = useToastStore(s => s.addToast)
  const [studentId, setStudentId] = useState('')
  const [programId, setProgramId] = useState('')
  const [institutionId, setInstitutionId] = useState('')

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
    mutationFn: verifyInstitution,
    onSuccess: () => { addToast('Institution verified', 'success'); setInstitutionId('') },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Tools</h1>
        <p className="text-sm text-gray-500">Administrative actions and system maintenance</p>
      </div>

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
