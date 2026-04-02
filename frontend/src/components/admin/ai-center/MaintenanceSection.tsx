import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  bootstrapPrograms, refreshStudent, refreshProgram, verifyInstitution,
} from '../../../api/admin'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Input from '../../ui/Input'
import { useToastStore } from '../../../stores/toast-store'
import { Cpu, RefreshCw, Building2, GraduationCap, User, CheckCircle } from 'lucide-react'

export default function MaintenanceSection() {
  const qc = useQueryClient()
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
    mutationFn: (id: string) => verifyInstitution(id),
    onSuccess: () => { addToast('Institution verified', 'success'); setInstitutionId(''); qc.invalidateQueries({ queryKey: ['admin'] }) },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  return (
    <div className="space-y-6">
      <Card className="p-4 bg-blue-50 border-blue-200">
        <h3 className="text-sm font-semibold text-blue-900 mb-1">Maintenance & Bootstrap</h3>
        <p className="text-sm text-blue-800">
          Run bulk AI operations, refresh individual entity features, or verify institutions.
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-green-100 text-green-600"><Building2 size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Verify Institution</h3>
              <p className="text-xs text-gray-500">Mark an institution as verified</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input value={institutionId} onChange={e => setInstitutionId(e.target.value)} placeholder="Institution UUID" className="flex-1" />
            <Button onClick={() => verifyMut.mutate(institutionId)} disabled={verifyMut.isPending || !institutionId}>
              <CheckCircle size={14} className="mr-1" /> Verify
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600"><User size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Refresh Student Features</h3>
              <p className="text-xs text-gray-500">Re-extract AI features for a specific student</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input value={studentId} onChange={e => setStudentId(e.target.value)} placeholder="Student UUID" className="flex-1" />
            <Button onClick={() => refreshStudentMut.mutate(studentId)} disabled={refreshStudentMut.isPending || !studentId}>
              <RefreshCw size={14} className="mr-1" /> Refresh
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-purple-100 text-purple-600"><GraduationCap size={20} /></div>
            <div>
              <h3 className="font-semibold text-gray-900">Refresh Program Features</h3>
              <p className="text-xs text-gray-500">Re-extract AI features for a specific program</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input value={programId} onChange={e => setProgramId(e.target.value)} placeholder="Program UUID" className="flex-1" />
            <Button onClick={() => refreshProgramMut.mutate(programId)} disabled={refreshProgramMut.isPending || !programId}>
              <RefreshCw size={14} className="mr-1" /> Refresh
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
