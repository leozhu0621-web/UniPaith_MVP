import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Trash2, Download, Eye, Database } from 'lucide-react'
import {
  getDatasets, requestDatasetUpload, confirmDatasetUpload,
  getDatasetPreview, updateDataset, deleteDataset,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import type { InstitutionDataset, DatasetPreview } from '../../types'

const DATASET_TYPES = [
  { value: 'admissions_history', label: 'Admissions History' },
  { value: 'prospect_list', label: 'Prospect List' },
  { value: 'outcomes_summary', label: 'Outcomes Summary' },
]

const USAGE_SCOPES = [
  { value: '', label: 'Not specified' },
  { value: 'marketing', label: 'Marketing only' },
  { value: 'analytics', label: 'Analytics only' },
  { value: 'admissions', label: 'Admissions only' },
  { value: 'all', label: 'All' },
]

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  pending: 'warning',
  validated: 'info',
  active: 'success',
  archived: 'neutral',
}

const COLUMN_FIELDS: Record<string, string[]> = {
  prospect_list: ['email', 'first_name', 'last_name', 'phone', 'nationality', 'country', 'degree_interest', 'program_interest', 'source', 'notes'],
  admissions_history: ['student_email', 'program_name', 'application_date', 'decision', 'gpa', 'test_score', 'enrollment_status'],
  outcomes_summary: ['program_name', 'graduation_year', 'employment_status', 'employer', 'salary_range', 'time_to_employment'],
}

export default function DataUploadPage() {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [previewTarget, setPreviewTarget] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<InstitutionDataset | null>(null)
  const [mappingTarget, setMappingTarget] = useState<InstitutionDataset | null>(null)

  // Upload form state
  const [name, setName] = useState('')
  const [type, setType] = useState('prospect_list')
  const [description, setDescription] = useState('')
  const [scope, setScope] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  // Mapping state
  const [columnMap, setColumnMap] = useState<Record<string, string>>({})

  const datasetsQ = useQuery({ queryKey: ['datasets'], queryFn: getDatasets })
  const datasets: InstitutionDataset[] = Array.isArray(datasetsQ.data) ? datasetsQ.data : []

  const previewQ = useQuery({
    queryKey: ['dataset-preview', previewTarget],
    queryFn: () => getDatasetPreview(previewTarget!),
    enabled: !!previewTarget,
  })
  const preview: DatasetPreview | undefined = previewQ.data

  const deleteMut = useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Dataset deleted', 'success')
      setDeleteTarget(null)
    },
    onError: () => showToast('Failed to delete', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateDataset(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Mapping saved', 'success')
      setMappingTarget(null)
    },
    onError: () => showToast('Failed to save mapping', 'error'),
  })

  const resetForm = () => {
    setName(''); setType('prospect_list'); setDescription(''); setScope(''); setSelectedFile(null)
  }

  const handleUpload = async () => {
    if (!name.trim() || !selectedFile) {
      showToast('Name and file are required', 'warning')
      return
    }
    setUploading(true)
    try {
      const { dataset_id, upload_url } = await requestDatasetUpload({
        dataset_name: name,
        dataset_type: type,
        file_name: selectedFile.name,
        content_type: selectedFile.type || 'text/csv',
        file_size_bytes: selectedFile.size,
        description: description || undefined,
        usage_scope: scope || undefined,
      })

      // Upload file to S3 presigned URL
      await fetch(upload_url, {
        method: 'PUT',
        body: selectedFile,
        headers: { 'Content-Type': selectedFile.type || 'text/csv' },
      })

      await confirmDatasetUpload(dataset_id)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Dataset uploaded!', 'success')
      setShowUploadModal(false)
      resetForm()
    } catch {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  const openMapping = (ds: InstitutionDataset) => {
    setMappingTarget(ds)
    setColumnMap(ds.column_mapping || {})
    setPreviewTarget(ds.id)
  }

  const saveMapping = () => {
    if (!mappingTarget) return
    updateMut.mutate({
      id: mappingTarget.id,
      payload: { column_mapping: columnMap, status: 'active' },
    })
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Data Upload"
        description="Upload and manage institution datasets for segmentation, campaigns, and analytics."
        actions={(
          <Button onClick={() => { resetForm(); setShowUploadModal(true) }} className="flex items-center gap-2">
            <Upload size={16} /> Upload Dataset
          </Button>
        )}
      />

      {datasetsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : datasets.length === 0 ? (
        <EmptyState
          icon={<Database size={40} />}
          title="No datasets"
          description="Upload CSV files with admissions history, prospect lists, or outcomes data."
          action={{ label: 'Upload Dataset', onClick: () => { resetForm(); setShowUploadModal(true) } }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {datasets.map(ds => (
            <Card key={ds.id} className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{ds.dataset_name}</h3>
                  <p className="text-xs text-gray-500">{ds.file_name}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={STATUS_BADGE[ds.status] ?? 'neutral'}>{ds.status}</Badge>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                <Badge variant="info">{DATASET_TYPES.find(t => t.value === ds.dataset_type)?.label ?? ds.dataset_type}</Badge>
                {ds.row_count != null && <span>{ds.row_count.toLocaleString()} rows</span>}
                {ds.usage_scope && <span>Scope: {ds.usage_scope}</span>}
                <span>v{ds.version}</span>
              </div>
              {ds.description && <p className="text-xs text-gray-400 mb-3 line-clamp-2">{ds.description}</p>}
              <p className="text-xs text-gray-400 mb-3">Uploaded {formatDate(ds.created_at)}</p>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setPreviewTarget(ds.id)} className="flex items-center gap-1">
                  <Eye size={14} /> Preview
                </Button>
                <Button variant="ghost" size="sm" onClick={() => openMapping(ds)} className="flex items-center gap-1">
                  <FileText size={14} /> Map Columns
                </Button>
                {ds.download_url && (
                  <a href={ds.download_url} target="_blank" rel="noopener noreferrer">
                    <Button variant="ghost" size="sm" className="flex items-center gap-1">
                      <Download size={14} /> Download
                    </Button>
                  </a>
                )}
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(ds)} className="flex items-center gap-1 text-red-600">
                  <Trash2 size={14} /> Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Upload Dataset">
        <div className="space-y-4">
          <Input label="Dataset Name *" value={name} onChange={e => setName(e.target.value)} />
          <Select label="Type" options={DATASET_TYPES} value={type} onChange={e => setType(e.target.value)} />
          <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={2} />
          <Select label="Usage Scope" options={USAGE_SCOPES} value={scope} onChange={e => setScope(e.target.value)} />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CSV File *</label>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
            />
            {selectedFile && <p className="text-xs text-gray-400 mt-1">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowUploadModal(false)}>Cancel</Button>
            <Button onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={!!previewTarget && !mappingTarget} onClose={() => setPreviewTarget(null)} title="Dataset Preview">
        {previewQ.isLoading ? (
          <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
        ) : !preview || preview.columns.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No data available. The file may still be uploading.</p>
        ) : (
          <div>
            <p className="text-xs text-gray-500 mb-3">{preview.total_rows.toLocaleString()} total rows, showing first {preview.rows.length}</p>
            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-50 text-left">
                    {preview.columns.map(col => (
                      <th key={col} className="px-2 py-1.5 font-medium text-gray-600 whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      {preview.columns.map(col => (
                        <td key={col} className="px-2 py-1.5 text-gray-700 whitespace-nowrap max-w-[200px] truncate">{row[col] ?? ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Modal>

      {/* Column Mapping Modal */}
      <Modal isOpen={!!mappingTarget} onClose={() => { setMappingTarget(null); setPreviewTarget(null) }} title="Map Columns">
        {previewQ.isLoading ? (
          <Skeleton className="h-40" />
        ) : !preview ? (
          <p className="text-sm text-gray-500">Loading preview...</p>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-gray-500">Map each CSV column to a platform field. Unmapped columns will be ignored.</p>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {preview.columns.map(col => {
                const fieldOptions = COLUMN_FIELDS[mappingTarget?.dataset_type ?? 'prospect_list'] ?? []
                return (
                  <div key={col} className="flex items-center gap-3">
                    <span className="text-sm text-gray-700 w-40 truncate font-mono">{col}</span>
                    <span className="text-gray-400">&rarr;</span>
                    <select
                      value={columnMap[col] || ''}
                      onChange={e => setColumnMap(prev => ({ ...prev, [col]: e.target.value }))}
                      className="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                    >
                      <option value="">— skip —</option>
                      {fieldOptions.map(f => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </select>
                  </div>
                )
              })}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => { setMappingTarget(null); setPreviewTarget(null) }}>Cancel</Button>
              <Button onClick={saveMapping} disabled={updateMut.isPending}>
                {updateMut.isPending ? 'Saving...' : 'Save Mapping'}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Dataset">
        <p className="text-sm text-gray-600 mb-4">
          Delete <strong>{deleteTarget?.dataset_name}</strong>? This removes the file from storage permanently.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
