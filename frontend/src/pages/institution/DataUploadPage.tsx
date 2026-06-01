import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Upload, Database, Eye, Pencil, RefreshCw, Plus, History, Download, Trash2,
  MoreHorizontal, RotateCcw, Table2, BarChart3, UploadCloud,
} from 'lucide-react'
import {
  getDatasets, getDatasetPreview, updateDataset, deleteDataset,
  getDatasetVersions, rollbackDataset, exportDataset,
  uploadDatasetFile, replaceDataset, appendDataset,
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
import Dropdown from '../../components/ui/Dropdown'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatRelative } from '../../utils/format'
import type { InstitutionDataset, DatasetPreview, DatasetVersion } from '../../types'
import { DATASET_TYPES, USAGE_SCOPES, STATUS_BADGE, SCOPE_LABEL, USED_BY } from './data-upload/constants'
import HistogramBars from './data-upload/HistogramBars'
import UploadWizard from './data-upload/UploadWizard'

const FILTERS = [{ value: 'all', label: 'All datasets' }, ...DATASET_TYPES.map((t) => ({ value: t.value, label: t.label }))]

export default function DataUploadPage() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState('all')
  const [showWizard, setShowWizard] = useState(false)
  const [previewTarget, setPreviewTarget] = useState<InstitutionDataset | null>(null)
  const [versionsTarget, setVersionsTarget] = useState<InstitutionDataset | null>(null)
  const [editTarget, setEditTarget] = useState<InstitutionDataset | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<InstitutionDataset | null>(null)
  const [fileTarget, setFileTarget] = useState<{ ds: InstitutionDataset; mode: 'replace' | 'append' } | null>(null)

  const datasetsQ = useQuery({ queryKey: ['datasets', filter], queryFn: () => getDatasets(filter) })
  const datasets = datasetsQ.data ?? []

  const invalidate = () => qc.invalidateQueries({ queryKey: ['datasets'] })

  async function handleExport(ds: InstitutionDataset) {
    try {
      const { blob, fileName } = await exportDataset(ds.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      showToast('Export failed.', 'error')
    }
  }

  return (
    <div className="space-y-4 p-6">
      <InstitutionPageHeader
        title="Data"
        description="Upload your own datasets to power matching, campaigns, and analytics."
        actions={
          <Button variant="secondary" onClick={() => setShowWizard(true)}>
            <Upload size={16} /> Upload dataset
          </Button>
        }
      />

      <div className="flex items-center gap-3">
        <div className="w-52">
          <Select value={filter} onChange={(e) => setFilter(e.target.value)} options={FILTERS} uiSize="sm" />
        </div>
        {!datasetsQ.isLoading && (
          <span className="text-xs text-muted-foreground">
            {datasets.length} dataset{datasets.length === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {datasetsQ.isLoading ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : datasets.length === 0 ? (
        <EmptyState
          icon={<Database size={40} />}
          title="No datasets yet"
          description="Upload a dataset to power matching, campaigns, or analytics."
          action={{ label: 'Upload dataset', onClick: () => setShowWizard(true) }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {datasets.map((ds) => (
            <DatasetCard
              key={ds.id}
              ds={ds}
              onPreview={() => setPreviewTarget(ds)}
              onEdit={() => setEditTarget(ds)}
              onReplace={() => setFileTarget({ ds, mode: 'replace' })}
              onAppend={() => setFileTarget({ ds, mode: 'append' })}
              onVersions={() => setVersionsTarget(ds)}
              onExport={() => handleExport(ds)}
              onDelete={() => setDeleteTarget(ds)}
            />
          ))}
        </div>
      )}

      <UploadWizard isOpen={showWizard} onClose={() => setShowWizard(false)} onComplete={invalidate} />
      {previewTarget && <PreviewModal ds={previewTarget} onClose={() => setPreviewTarget(null)} />}
      {versionsTarget && (
        <VersionsModal ds={versionsTarget} onClose={() => setVersionsTarget(null)} onChange={invalidate} />
      )}
      {editTarget && <EditModal ds={editTarget} onClose={() => setEditTarget(null)} onSaved={invalidate} />}
      {deleteTarget && <DeleteModal ds={deleteTarget} onClose={() => setDeleteTarget(null)} onDeleted={invalidate} />}
      {fileTarget && (
        <FileModal {...fileTarget} onClose={() => setFileTarget(null)} onDone={invalidate} />
      )}
    </div>
  )
}

function DatasetCard({ ds, onPreview, onEdit, onReplace, onAppend, onVersions, onExport, onDelete }: {
  ds: InstitutionDataset
  onPreview: () => void; onEdit: () => void; onReplace: () => void; onAppend: () => void
  onVersions: () => void; onExport: () => void; onDelete: () => void
}) {
  const typeLabel = DATASET_TYPES.find((t) => t.value === ds.dataset_type)?.label ?? ds.dataset_type
  return (
    <Card className="p-4">
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="min-w-0 truncate font-semibold text-foreground" title={ds.dataset_name}>
          {ds.dataset_name}
        </h3>
        <Badge variant={STATUS_BADGE[ds.status] ?? 'neutral'}>{ds.status}</Badge>
      </div>
      <p className="text-xs text-muted-foreground">
        {typeLabel} · {(ds.row_count ?? 0).toLocaleString()} rows · v{ds.version}
      </p>
      <p className="mt-0.5 text-xs text-muted-foreground">
        Updated {formatRelative(ds.updated_at)} · Used by: {USED_BY[ds.dataset_type]}
        {ds.usage_scope ? ` · Scope: ${SCOPE_LABEL[ds.usage_scope] ?? ds.usage_scope}` : ''}
      </p>
      {ds.description && <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{ds.description}</p>}

      <div className="mt-3 flex items-center gap-2">
        <Button variant="tertiary" size="sm" onClick={onPreview}><Eye size={14} /> Preview</Button>
        <Button variant="ghost" size="sm" onClick={onVersions}><History size={14} /> Versions</Button>
        <div className="ml-auto">
          <Dropdown
            trigger={<Button variant="ghost" size="sm" aria-label="More actions"><MoreHorizontal size={16} /></Button>}
            items={[
              { label: 'Edit', icon: <Pencil size={14} />, onClick: onEdit },
              { label: 'Replace', icon: <RefreshCw size={14} />, onClick: onReplace },
              { label: 'Append rows', icon: <Plus size={14} />, onClick: onAppend },
              { label: 'Export CSV', icon: <Download size={14} />, onClick: onExport },
              { label: 'Delete', icon: <Trash2 size={14} />, onClick: onDelete, variant: 'danger' },
            ]}
          />
        </div>
      </div>
    </Card>
  )
}

function PreviewModal({ ds, onClose }: { ds: InstitutionDataset; onClose: () => void }) {
  const [view, setView] = useState<'rows' | 'columns'>('rows')
  const previewQ = useQuery({ queryKey: ['dataset-preview', ds.id], queryFn: () => getDatasetPreview(ds.id) })
  const preview = previewQ.data as DatasetPreview | undefined

  return (
    <Modal isOpen onClose={onClose} title={`Preview · ${ds.dataset_name}`} size="lg">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {preview ? `${preview.total_rows.toLocaleString()} rows · showing ${preview.rows.length}` : ' '}
        </p>
        <div className="flex gap-1 rounded-md border border-border p-0.5">
          <button onClick={() => setView('rows')}
            className={`flex items-center gap-1 rounded px-2 py-1 text-xs ${view === 'rows' ? 'bg-muted text-foreground' : 'text-muted-foreground'}`}>
            <Table2 size={13} /> Rows
          </button>
          <button onClick={() => setView('columns')}
            className={`flex items-center gap-1 rounded px-2 py-1 text-xs ${view === 'columns' ? 'bg-muted text-foreground' : 'text-muted-foreground'}`}>
            <BarChart3 size={13} /> Columns
          </button>
        </div>
      </div>

      {previewQ.isLoading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-7" />)}</div>
      ) : !preview || preview.columns.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">No data to preview.</p>
      ) : view === 'rows' ? (
        <div className="max-h-96 overflow-auto rounded-md border border-border">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-muted">
              <tr className="text-left">
                {preview.columns.map((c) => (
                  <th key={c} className="whitespace-nowrap px-2.5 py-2 font-semibold text-foreground">{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row, i) => (
                <tr key={i} className="border-t border-border">
                  {preview.columns.map((c) => (
                    <td key={c} className="max-w-[220px] truncate whitespace-nowrap px-2.5 py-1.5 text-muted-foreground">
                      {row[c] ?? ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid max-h-96 grid-cols-1 gap-4 overflow-y-auto sm:grid-cols-2">
          {preview.columns.map((c) => (
            <div key={c} className="rounded-md border border-border p-3">
              <p className="mb-2 truncate font-mono text-xs font-semibold text-foreground">{c}</p>
              <HistogramBars col={preview.histogram[c] ?? { top: [], null_count: 0, distinct: 0 }} />
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}

function VersionsModal({ ds, onClose, onChange }: { ds: InstitutionDataset; onClose: () => void; onChange: () => void }) {
  const qc = useQueryClient()
  const versionsQ = useQuery({ queryKey: ['dataset-versions', ds.id], queryFn: () => getDatasetVersions(ds.id) })
  const versions = (versionsQ.data ?? []) as DatasetVersion[]
  const latest = versions.length ? versions[0].version_number : 0

  const rollbackMut = useMutation({
    mutationFn: (n: number) => rollbackDataset(ds.id, n),
    onSuccess: () => {
      showToast('Rolled back.', 'success')
      qc.invalidateQueries({ queryKey: ['dataset-versions', ds.id] })
      qc.invalidateQueries({ queryKey: ['dataset-preview', ds.id] })
      onChange()
    },
    onError: () => showToast('Rollback failed.', 'error'),
  })

  return (
    <Modal isOpen onClose={onClose} title={`Version history · ${ds.dataset_name}`} size="md">
      {versionsQ.isLoading ? (
        <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14" />)}</div>
      ) : (
        <div className="space-y-2">
          {versions.map((v) => {
            const cs = v.changes_summary
            return (
              <div key={v.id} className="flex items-center justify-between rounded-md border border-border p-3">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 text-sm font-medium text-foreground">
                    v{v.version_number}
                    {v.version_number === latest && <Badge variant="info">current</Badge>}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(v.row_count ?? 0).toLocaleString()} rows · {formatRelative(v.uploaded_at)}
                  </p>
                  {cs && (
                    <p className="text-[11px] text-muted-foreground">
                      {cs.note
                        ? cs.note
                        : `${cs.added ?? 0} added · ${cs.modified ?? 0} modified · ${cs.invalidated ?? 0} invalidated`}
                    </p>
                  )}
                </div>
                {v.version_number !== latest && (
                  <Button variant="tertiary" size="sm" loading={rollbackMut.isPending}
                    onClick={() => rollbackMut.mutate(v.version_number)}>
                    <RotateCcw size={13} /> Roll back
                  </Button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </Modal>
  )
}

function EditModal({ ds, onClose, onSaved }: { ds: InstitutionDataset; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(ds.dataset_name)
  const [description, setDescription] = useState(ds.description ?? '')
  const [scope, setScope] = useState<string>(ds.usage_scope ?? 'all')
  const mut = useMutation({
    mutationFn: () => updateDataset(ds.id, { dataset_name: name, description, usage_scope: scope }),
    onSuccess: () => { showToast('Saved.', 'success'); onSaved(); onClose() },
    onError: () => showToast('Could not save.', 'error'),
  })
  return (
    <Modal isOpen onClose={onClose} title="Edit dataset" size="md"
      footer={
        <div className="flex w-full justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="secondary" onClick={() => mut.mutate()} loading={mut.isPending}>Save</Button>
        </div>
      }>
      <div className="space-y-3">
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <Textarea label="Description" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        <Select label="Usage scope" value={scope} onChange={(e) => setScope(e.target.value)} options={USAGE_SCOPES} />
      </div>
    </Modal>
  )
}

function DeleteModal({ ds, onClose, onDeleted }: { ds: InstitutionDataset; onClose: () => void; onDeleted: () => void }) {
  const mut = useMutation({
    mutationFn: () => deleteDataset(ds.id),
    onSuccess: () => { showToast('Dataset deleted.', 'success'); onDeleted(); onClose() },
    onError: () => showToast('Could not delete.', 'error'),
  })
  return (
    <Modal isOpen onClose={onClose} title="Delete dataset" size="sm"
      footer={
        <div className="flex w-full justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="destructive" onClick={() => mut.mutate()} loading={mut.isPending}>Delete</Button>
        </div>
      }>
      <p className="text-sm text-muted-foreground">
        Delete <strong className="text-foreground">{ds.dataset_name}</strong> and all its versions? This permanently
        removes the files from storage and is audit-logged. This cannot be undone.
      </p>
    </Modal>
  )
}

function FileModal({ ds, mode, onClose, onDone }: {
  ds: InstitutionDataset; mode: 'replace' | 'append'; onClose: () => void; onDone: () => void
}) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit() {
    if (!file) { showToast('Choose a file.', 'warning'); return }
    setBusy(true)
    try {
      const { file_ref } = await uploadDatasetFile(file)
      if (mode === 'replace') {
        await replaceDataset(ds.id, { file_ref, file_name: file.name })
      } else {
        await appendDataset(ds.id, { file_ref, file_name: file.name })
      }
      showToast(mode === 'replace' ? 'Dataset replaced.' : 'Rows appended.', 'success')
      onDone()
      onClose()
    } catch {
      showToast(`${mode === 'replace' ? 'Replace' : 'Append'} failed.`, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal isOpen onClose={onClose} title={mode === 'replace' ? 'Replace this dataset?' : 'Append rows'} size="md"
      footer={
        <div className="flex w-full justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="secondary" onClick={submit} loading={busy} disabled={!file}>
            {mode === 'replace' ? 'Replace' : 'Append'}
          </Button>
        </div>
      }>
      <p className="mb-3 text-xs text-muted-foreground">
        {mode === 'replace'
          ? 'Upload a new file to replace the current data. The existing column mapping is reused; a new version is recorded.'
          : 'Upload a file whose rows are added to this dataset. A new version is recorded.'}
      </p>
      <button type="button" onClick={() => fileInput.current?.click()}
        className="flex w-full flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border py-8 text-muted-foreground transition-colors hover:border-secondary hover:text-secondary">
        <UploadCloud size={24} />
        <span className="text-sm font-medium">{file ? file.name : 'Choose a CSV, TSV, or xlsx file'}</span>
      </button>
      <input ref={fileInput} type="file" accept=".csv,.tsv,.xlsx,.xlsm" className="hidden"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
    </Modal>
  )
}
