import { useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Eye, Pencil, RefreshCw, Plus, Trash2, Download, Database, History, FilePlus,
} from 'lucide-react'
import {
  confirmDatasetReplace,
  confirmDatasetUpload,
  deleteDataset,
  getDatasetMappingTemplates,
  getDatasetPreview,
  getDataset,
  getDatasets,
  getDatasetVersions,
  parseValidationReport,
  requestDatasetReplaceUpload,
  requestDatasetUpload,
  rollbackDatasetVersion,
  updateDataset,
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
import Table from '../../components/ui/Table'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatRelative } from '../../utils/format'
import type {
  DatasetMappingTemplate,
  DatasetPreview,
  DatasetStatus,
  InstitutionDataset,
  ValidationReport,
} from '../../types'

const DATASET_TYPES = [
  { value: 'admissions_history', label: 'Admissions History' },
  { value: 'prospect_list', label: 'Prospect List' },
  { value: 'outcomes_summary', label: 'Outcomes Summary' },
]

const USAGE_SCOPES = [
  { value: 'marketing', label: 'Marketing only' },
  { value: 'admissions', label: 'Admissions ops only' },
  { value: 'analytics', label: 'Analytics only' },
  { value: 'all', label: 'All' },
]

const TYPE_FILTER = [
  { value: 'all', label: 'All' },
  ...DATASET_TYPES,
]

const COLUMN_FIELDS: Record<string, string[]> = {
  prospect_list: ['email', 'first_name', 'last_name', 'phone', 'nationality', 'country', 'degree_interest', 'program_interest', 'source', 'notes'],
  admissions_history: ['student_email', 'program_name', 'application_date', 'decision', 'gpa', 'test_score', 'enrollment_status'],
  outcomes_summary: ['program_name', 'graduation_year', 'employment_status', 'employer', 'salary_range', 'time_to_employment'],
}

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning' | 'danger'> = {
  uploaded: 'warning',
  pending: 'warning',
  validated: 'info',
  processed: 'success',
  active: 'success',
  failed: 'danger',
  archived: 'neutral',
}

function displayStatus(status: DatasetStatus): string {
  if (status === 'pending') return 'uploaded'
  if (status === 'active') return 'processed'
  return status
}

function typeLabel(t: string) {
  return DATASET_TYPES.find(x => x.value === t)?.label ?? t
}

function uploadFileToUrl(url: string, file: File) {
  return fetch(url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': file.type || 'text/csv' },
  })
}

async function parseLocalCsvColumns(file: File): Promise<string[]> {
  const slice = file.slice(0, 8192)
  const text = await slice.text()
  const line = text.split(/\r?\n/)[0] ?? ''
  const delim = line.includes('\t') ? '\t' : ','
  return line.split(delim).map(s => s.trim().replace(/^"|"$/g, '')).filter(Boolean)
}

function ValidationReportPanel({ report }: { report: ValidationReport }) {
  const sections: { title: string; items: { row: number; detail: string }[] }[] = [
    {
      title: 'Missing required fields',
      items: (report.missing_required ?? []).map(i => ({
        row: i.row,
        detail: i.field,
      })),
    },
    {
      title: 'Duplicate rows',
      items: (report.duplicates ?? []).map(i => ({
        row: i.row,
        detail: i.duplicate_of_row ? `duplicate of row ${i.duplicate_of_row}` : 'duplicate key',
      })),
    },
    {
      title: 'Invalid dates',
      items: (report.invalid_dates ?? []).map(i => ({
        row: i.row,
        detail: `${i.field}: "${i.value}"`,
      })),
    },
    {
      title: 'Unmappable program identifiers',
      items: (report.unmappable_programs ?? []).map(i => ({
        row: i.row,
        detail: `${i.value}${i.suggestions?.length ? ` → try ${i.suggestions.join(', ')}` : ''}`,
      })),
    },
  ].filter(s => s.items.length > 0)

  return (
    <div className="space-y-3 max-h-64 overflow-y-auto text-sm">
      {sections.map(s => (
        <div key={s.title}>
          <p className="font-medium text-foreground">{s.title}</p>
          <ul className="mt-1 space-y-0.5 text-muted-foreground">
            {s.items.slice(0, 20).map((item, idx) => (
              <li key={`${s.title}-${idx}`}>Row {item.row}: {item.detail}</li>
            ))}
            {s.items.length > 20 && (
              <li className="text-xs">…and {s.items.length - 20} more</li>
            )}
          </ul>
        </div>
      ))}
    </div>
  )
}

export default function DataUploadPage() {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)

  const [typeFilter, setTypeFilter] = useState('all')
  const [wizardOpen, setWizardOpen] = useState(false)
  const [wizardMode, setWizardMode] = useState<'create' | 'replace' | 'append'>('create')
  const [wizardStep, setWizardStep] = useState(0)
  const [targetDataset, setTargetDataset] = useState<InstitutionDataset | null>(null)

  const [name, setName] = useState('')
  const [type, setType] = useState('prospect_list')
  const [description, setDescription] = useState('')
  const [coverageStart, setCoverageStart] = useState('')
  const [coverageEnd, setCoverageEnd] = useState('')
  const [updateMode, setUpdateMode] = useState<'replace' | 'append'>('replace')
  const [scope, setScope] = useState('all')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [columnMap, setColumnMap] = useState<Record<string, string>>({})
  const [saveTemplate, setSaveTemplate] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [pendingDatasetId, setPendingDatasetId] = useState<string | null>(null)
  const [stagingKey, setStagingKey] = useState<string | null>(null)
  const [localColumns, setLocalColumns] = useState<string[]>([])

  const [previewTarget, setPreviewTarget] = useState<string | null>(null)
  const [editTarget, setEditTarget] = useState<InstitutionDataset | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<InstitutionDataset | null>(null)
  const [versionsTarget, setVersionsTarget] = useState<InstitutionDataset | null>(null)
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null)
  const [validationAction, setValidationAction] = useState<(() => Promise<void>) | null>(null)

  const datasetsQ = useQuery({ queryKey: ['datasets'], queryFn: getDatasets })
  const templatesQ = useQuery({
    queryKey: ['dataset-mapping-templates', type],
    queryFn: () => getDatasetMappingTemplates(type),
    enabled: wizardOpen,
  })

  const datasets: InstitutionDataset[] = Array.isArray(datasetsQ.data) ? datasetsQ.data : []
  const filtered = useMemo(() => {
    if (typeFilter === 'all') return datasets
    return datasets.filter(d => d.dataset_type === typeFilter)
  }, [datasets, typeFilter])

  const previewQ = useQuery({
    queryKey: ['dataset-preview', previewTarget],
    queryFn: () => getDatasetPreview(previewTarget!, 100),
    enabled: !!previewTarget,
  })
  const preview: DatasetPreview | undefined = previewQ.data

  const wizardPreviewQ = useQuery({
    queryKey: ['dataset-preview-wizard', pendingDatasetId],
    queryFn: () => getDatasetPreview(pendingDatasetId!, 100),
    enabled: !!pendingDatasetId && wizardStep >= 3,
  })

  const versionsQ = useQuery({
    queryKey: ['dataset-versions', versionsTarget?.id],
    queryFn: () => getDatasetVersions(versionsTarget!.id),
    enabled: !!versionsTarget,
  })

  const deleteMut = useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Dataset deleted', 'success')
      setDeleteTarget(null)
    },
    onError: () => showToast('Failed to delete dataset', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof updateDataset>[1] }) =>
      updateDataset(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Dataset updated', 'success')
      setEditTarget(null)
    },
    onError: () => showToast('Failed to update dataset', 'error'),
  })

  const rollbackMut = useMutation({
    mutationFn: ({ datasetId, versionId }: { datasetId: string; versionId: string }) =>
      rollbackDatasetVersion(datasetId, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      queryClient.invalidateQueries({ queryKey: ['dataset-versions'] })
      showToast('Rolled back to prior version', 'success')
    },
    onError: () => showToast('Rollback failed', 'error'),
  })

  const resetWizard = () => {
    setWizardStep(0)
    setName('')
    setType('prospect_list')
    setDescription('')
    setCoverageStart('')
    setCoverageEnd('')
    setUpdateMode('replace')
    setScope('all')
    setSelectedFile(null)
    setColumnMap({})
    setSaveTemplate(false)
    setTemplateName('')
    setPendingDatasetId(null)
    setStagingKey(null)
    setLocalColumns([])
    setUploadProgress(0)
    setTargetDataset(null)
  }

  const openCreateWizard = () => {
    resetWizard()
    setWizardMode('create')
    setWizardOpen(true)
  }

  const openReplaceWizard = (ds: InstitutionDataset, mode: 'replace' | 'append') => {
    resetWizard()
    setWizardMode(mode)
    setTargetDataset(ds)
    setName(ds.dataset_name)
    setType(ds.dataset_type)
    setDescription(ds.description ?? '')
    setScope(ds.usage_scope ?? 'all')
    setColumnMap(ds.column_mapping ?? {})
    setUpdateMode(mode)
    setWizardOpen(true)
  }

  const applyTemplate = (tpl: DatasetMappingTemplate) => {
    setColumnMap(tpl.column_mapping)
    showToast(`Applied template "${tpl.template_name}"`, 'success')
  }

  const suggestMapping = (columns: string[]) => {
    const fields = COLUMN_FIELDS[type] ?? []
    const next: Record<string, string> = { ...columnMap }
    for (const col of columns) {
      if (next[col]) continue
      const norm = col.toLowerCase().replace(/[^a-z0-9]/g, '_')
      const match = fields.find(f => f === norm || norm.includes(f) || f.includes(norm))
      if (match) next[col] = match
    }
    setColumnMap(next)
  }

  const runUpload = async (skipInvalid = false) => {
    if (!selectedFile) {
      showToast('Choose a file to upload', 'warning')
      return
    }
    setUploading(true)
    setUploadProgress(15)
    try {
      let datasetId = pendingDatasetId
      let staging = stagingKey

      if (wizardMode === 'create') {
        const init = await requestDatasetUpload({
          dataset_name: name.trim(),
          dataset_type: type,
          file_name: selectedFile.name,
          content_type: selectedFile.type || 'text/csv',
          file_size_bytes: selectedFile.size,
          description: description || undefined,
          usage_scope: scope,
          coverage_start: coverageStart || undefined,
          coverage_end: coverageEnd || undefined,
          update_mode: updateMode,
        })
        datasetId = init.dataset_id
        setUploadProgress(45)
        await uploadFileToUrl(init.upload_url, selectedFile)
        setUploadProgress(70)
        await confirmDatasetUpload(datasetId, {
          column_mapping: columnMap,
          skip_invalid_rows: skipInvalid,
          save_template: saveTemplate,
          template_name: saveTemplate ? templateName : undefined,
        })
      } else if (targetDataset && staging) {
        setUploadProgress(70)
        await confirmDatasetReplace(targetDataset.id, {
          staging_s3_key: staging,
          file_name: selectedFile.name,
          update_mode: wizardMode === 'append' ? 'append' : 'replace',
          column_mapping: columnMap,
          skip_invalid_rows: skipInvalid,
        })
        datasetId = targetDataset.id
      }

      setUploadProgress(100)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      showToast('Dataset processed successfully', 'success')
      setWizardOpen(false)
      resetWizard()
      setValidationReport(null)
    } catch (err) {
      const report = parseValidationReport(err)
      if (report && report.error_count) {
        setValidationReport(report)
        setValidationAction(() => async () => runUpload(true))
      } else {
        showToast('Upload failed — check file format and mapping', 'error')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleFileStepNext = async () => {
    if (!selectedFile) {
      showToast('Choose a CSV, TSV, or spreadsheet export', 'warning')
      return
    }
    if (wizardMode === 'create') {
      setUploading(true)
      setUploadProgress(20)
      try {
        const init = await requestDatasetUpload({
          dataset_name: name.trim(),
          dataset_type: type,
          file_name: selectedFile.name,
          content_type: selectedFile.type || 'text/csv',
          file_size_bytes: selectedFile.size,
          description: description || undefined,
          usage_scope: scope,
          coverage_start: coverageStart || undefined,
          coverage_end: coverageEnd || undefined,
        })
        await uploadFileToUrl(init.upload_url, selectedFile)
        setPendingDatasetId(init.dataset_id)
        setLocalColumns(await parseLocalCsvColumns(selectedFile))
        setUploadProgress(100)
        setWizardStep(3)
      } catch {
        showToast('File upload failed', 'error')
      } finally {
        setUploading(false)
        setUploadProgress(0)
      }
      return
    }
    if (targetDataset && selectedFile) {
      setUploading(true)
      setUploadProgress(20)
      try {
        const init = await requestDatasetReplaceUpload(targetDataset.id, {
          file_name: selectedFile.name,
          content_type: selectedFile.type || 'text/csv',
          file_size_bytes: selectedFile.size,
        })
        await uploadFileToUrl(init.upload_url, selectedFile)
        setStagingKey(init.staging_s3_key ?? null)
        setPendingDatasetId(targetDataset.id)
        const cols = await parseLocalCsvColumns(selectedFile)
        setLocalColumns(cols)
        setWizardStep(1)
      } catch {
        showToast('File upload failed', 'error')
      } finally {
        setUploading(false)
        setUploadProgress(0)
      }
      return
    }
    setWizardStep(3)
  }

  const columns = [
    {
      key: 'dataset_name',
      label: 'Dataset',
      render: (row: InstitutionDataset) => (
        <div className="min-w-0">
          <p className="font-medium text-foreground truncate">{row.dataset_name}</p>
          <p className="text-xs text-muted-foreground">
            {typeLabel(row.dataset_type)}
            {row.row_count != null ? ` · ${row.row_count.toLocaleString()} rows` : ''}
          </p>
        </div>
      ),
    },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (row: InstitutionDataset) => (
        <span className="text-muted-foreground">{formatRelative(row.updated_at)}</span>
      ),
    },
    {
      key: 'used_by',
      label: 'Used by',
      render: (row: InstitutionDataset) => (
        <span className="text-muted-foreground text-xs">
          {(row.used_by ?? []).join(', ') || '—'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (row: InstitutionDataset) => (
        <Badge variant={STATUS_BADGE[displayStatus(row.status)] ?? 'neutral'}>
          {displayStatus(row.status)}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (row: InstitutionDataset) => (
        <div className="flex flex-wrap gap-1 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setPreviewTarget(row.id)} aria-label="Preview">
            <Eye size={14} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setEditTarget(row)} aria-label="Edit">
            <Pencil size={14} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => openReplaceWizard(row, 'replace')} aria-label="Replace">
            <RefreshCw size={14} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => openReplaceWizard(row, 'append')} aria-label="Append">
            <FilePlus size={14} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setVersionsTarget(row)} aria-label="Versions">
            <History size={14} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Export"
            onClick={async () => {
              try {
                const ds = await getDataset(row.id)
                if (ds.download_url) {
                  window.open(ds.download_url, '_blank', 'noopener,noreferrer')
                } else {
                  showToast('Export unavailable', 'warning')
                }
              } catch {
                showToast('Export failed', 'error')
              }
            }}
          >
            <Download size={14} />
          </Button>
          <Button variant="ghost" size="sm" className="text-error" onClick={() => setDeleteTarget(row)} aria-label="Delete">
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ]

  const wizardSteps =
    wizardMode === 'create'
      ? ['Details', 'Update mode', 'File', 'Mapping', 'Scope', 'Submit']
      : ['File', 'Mapping', 'Submit']

  const stepIndex = wizardMode === 'create' ? wizardStep : wizardStep - 2

  return (
    <div className="p-6 space-y-4 max-w-6xl mx-auto">
      <header className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Data</p>
          <h1 className="text-2xl font-bold text-foreground">Your datasets</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload admissions history, prospect lists, and outcomes for matching, campaigns, and analytics.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-40">
            <Select
              label="Filter"
              options={TYPE_FILTER}
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
            />
          </div>
          <Button onClick={openCreateWizard} className="flex items-center gap-2">
            <Plus size={16} /> Upload dataset
          </Button>
        </div>
      </header>

      <Card>
        {datasetsQ.isLoading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Database size={40} />}
            title="No datasets yet"
            description="Upload a dataset to power matching, campaigns, or analytics."
            action={{ label: 'Upload dataset', onClick: openCreateWizard }}
          />
        ) : (
          <Table columns={columns} data={filtered} emptyMessage="No datasets match this filter." />
        )}
      </Card>

      {/* Upload wizard */}
      <Modal
        isOpen={wizardOpen}
        onClose={() => !uploading && setWizardOpen(false)}
        title={wizardMode === 'create' ? 'Upload dataset' : `${wizardMode === 'append' ? 'Append to' : 'Replace'} ${targetDataset?.dataset_name}`}
      >
        <div className="flex gap-1 mb-4 flex-wrap">
          {wizardSteps.map((label, i) => (
            <span
              key={label}
              className={`text-xs px-2 py-1 rounded-pill ${
                i === stepIndex ? 'bg-cobalt/10 text-cobalt font-semibold' : 'text-muted-foreground'
              }`}
            >
              {label}
            </span>
          ))}
        </div>

        {uploading && uploadProgress > 0 && (
          <div className="mb-4">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-cobalt transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">Upload in progress…</p>
          </div>
        )}

        {wizardMode === 'create' && wizardStep === 0 && (
          <div className="space-y-4">
            <Input label="Dataset name *" value={name} onChange={e => setName(e.target.value)} />
            <Select label="Type *" options={DATASET_TYPES} value={type} onChange={e => setType(e.target.value)} />
            <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={2} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Coverage start" type="date" value={coverageStart} onChange={e => setCoverageStart(e.target.value)} />
              <Input label="Coverage end" type="date" value={coverageEnd} onChange={e => setCoverageEnd(e.target.value)} />
            </div>
          </div>
        )}

        {wizardMode === 'create' && wizardStep === 1 && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Choose how this file updates the dataset.</p>
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={updateMode === 'replace'} onChange={() => setUpdateMode('replace')} />
              Replace dataset (full refresh)
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={updateMode === 'append'} onChange={() => setUpdateMode('append')} />
              Append new records
            </label>
          </div>
        )}

        {((wizardMode === 'create' && wizardStep === 2) || (wizardMode !== 'create' && wizardStep === 0)) && (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-foreground">File (CSV, TSV, or xlsx) *</label>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.tsv,.txt,.xlsx"
              onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-muted file:text-foreground"
            />
            {selectedFile && (
              <p className="text-xs text-muted-foreground">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</p>
            )}
          </div>
        )}

        {((wizardMode === 'create' && wizardStep === 3) || (wizardMode !== 'create' && wizardStep === 1)) && (
          <div className="space-y-4">
            <p className="text-sm font-medium text-foreground">Map your columns to platform fields</p>
            {(templatesQ.data ?? []).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {(templatesQ.data ?? []).map(tpl => (
                  <Button key={tpl.id} variant="tertiary" size="sm" onClick={() => applyTemplate(tpl)}>
                    {tpl.template_name}
                  </Button>
                ))}
              </div>
            )}
            {wizardPreviewQ.isLoading ? (
              <Skeleton className="h-40" />
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {(wizardPreviewQ.data?.columns ?? localColumns ?? Object.keys(columnMap)).map(col => {
                  const fieldOptions = COLUMN_FIELDS[type] ?? []
                  return (
                    <div key={col} className="flex items-center gap-3">
                      <span className="text-sm font-mono w-36 truncate text-foreground">{col}</span>
                      <span className="text-muted-foreground">→</span>
                      <select
                        value={columnMap[col] || ''}
                        onChange={e => setColumnMap(prev => ({ ...prev, [col]: e.target.value }))}
                        className="flex-1 px-2 py-1.5 text-sm border border-border rounded-md bg-background"
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
            )}
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => wizardPreviewQ.data?.columns && suggestMapping(wizardPreviewQ.data.columns)}
            >
              Suggest mappings
            </Button>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={saveTemplate} onChange={e => setSaveTemplate(e.target.checked)} />
              Save mapping as template for reuse
            </label>
            {saveTemplate && (
              <Input label="Template name" value={templateName} onChange={e => setTemplateName(e.target.value)} />
            )}
          </div>
        )}

        {wizardMode === 'create' && wizardStep === 4 && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Set where this dataset may be used.</p>
            <Select label="Usage scope *" options={USAGE_SCOPES} value={scope} onChange={e => setScope(e.target.value)} />
          </div>
        )}

        {((wizardMode === 'create' && wizardStep === 5) || (wizardMode !== 'create' && wizardStep === 2)) && (
          <p className="text-sm text-muted-foreground">
            Submit to validate rows and activate the dataset. Invalid rows can be skipped after review.
          </p>
        )}

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="ghost" onClick={() => setWizardOpen(false)} disabled={uploading}>Cancel</Button>
          {wizardStep > 0 && (
            <Button variant="tertiary" onClick={() => setWizardStep(s => s - 1)} disabled={uploading}>
              Back
            </Button>
          )}
          {((wizardMode === 'create' && wizardStep < 5) || (wizardMode !== 'create' && wizardStep < 2)) ? (
            <Button
              onClick={() => {
                if (wizardMode === 'create' && wizardStep === 2) {
                  void handleFileStepNext()
                } else if (wizardMode !== 'create' && wizardStep === 0) {
                  setWizardStep(1)
                } else {
                  setWizardStep(s => s + 1)
                }
              }}
              disabled={uploading || (wizardStep === 0 && wizardMode === 'create' && !name.trim())}
            >
              Next
            </Button>
          ) : (
            <Button onClick={() => void runUpload(false)} disabled={uploading}>
              {uploading ? 'Processing…' : 'Submit'}
            </Button>
          )}
        </div>
      </Modal>

      {/* Preview */}
      <Modal isOpen={!!previewTarget} onClose={() => setPreviewTarget(null)} title="Dataset preview">
        {previewQ.isLoading ? (
          <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
        ) : !preview ? (
          <p className="text-sm text-muted-foreground text-center py-4">No preview available yet.</p>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-muted-foreground">
              {preview.total_rows.toLocaleString()} total rows · showing first {preview.rows.length}
            </p>
            {preview.column_histogram && Object.keys(preview.column_histogram).length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {Object.entries(preview.column_histogram).slice(0, 4).map(([col, counts]) => (
                  <div key={col} className="rounded-lg border border-border p-2 bg-muted/30">
                    <p className="font-medium text-foreground mb-1">{col}</p>
                    {Object.entries(counts).map(([val, n]) => (
                      <p key={val} className="text-muted-foreground truncate">{val}: {n}</p>
                    ))}
                  </div>
                ))}
              </div>
            )}
            <div className="overflow-x-auto max-h-80 rounded-lg border border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-muted text-left">
                    {preview.columns.map(col => (
                      <th key={col} className="px-3 py-2 font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, i) => (
                    <tr key={i} className="border-t border-border even:bg-muted/20">
                      {preview.columns.map(col => (
                        <td key={col} className="px-3 py-2 text-foreground whitespace-nowrap max-w-[200px] truncate">{row[col] ?? ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Modal>

      {/* Edit */}
      <Modal isOpen={!!editTarget} onClose={() => setEditTarget(null)} title="Edit dataset">
        {editTarget && (
          <div className="space-y-4">
            <Input
              label="Name"
              defaultValue={editTarget.dataset_name}
              onChange={e => setEditTarget({ ...editTarget, dataset_name: e.target.value })}
            />
            <Textarea
              label="Description"
              defaultValue={editTarget.description ?? ''}
              onChange={e => setEditTarget({ ...editTarget, description: e.target.value })}
              rows={2}
            />
            <Select
              label="Usage scope"
              options={USAGE_SCOPES}
              value={editTarget.usage_scope ?? 'all'}
              onChange={e => setEditTarget({ ...editTarget, usage_scope: e.target.value })}
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditTarget(null)}>Cancel</Button>
              <Button
                onClick={() => updateMut.mutate({
                  id: editTarget.id,
                  payload: {
                    dataset_name: editTarget.dataset_name,
                    description: editTarget.description ?? undefined,
                    usage_scope: editTarget.usage_scope ?? undefined,
                  },
                })}
                disabled={updateMut.isPending}
              >
                Save
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete dataset?">
        <p className="text-sm text-muted-foreground mb-4">
          Delete <strong className="text-foreground">{deleteTarget?.dataset_name}</strong>? This removes the file from storage and is audit-logged. This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            variant="danger"
            onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
            disabled={deleteMut.isPending}
          >
            Delete
          </Button>
        </div>
      </Modal>

      {/* Versions */}
      <Modal isOpen={!!versionsTarget} onClose={() => setVersionsTarget(null)} title="Version history">
        {versionsQ.isLoading ? (
          <Skeleton className="h-32" />
        ) : (versionsQ.data ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">No versions recorded yet.</p>
        ) : (
          <ul className="space-y-3 max-h-80 overflow-y-auto">
            {(versionsQ.data ?? []).map(v => (
              <li key={v.id} className="flex items-start justify-between gap-3 border-b border-border pb-3">
                <div>
                  <p className="text-sm font-medium text-foreground">Version {v.version_number}</p>
                  <p className="text-xs text-muted-foreground">
                    {v.changes_summary.added} added · {v.changes_summary.modified} modified ·{' '}
                    {v.changes_summary.invalidated} invalidated
                  </p>
                  <p className="text-xs text-muted-foreground">{formatDate(v.created_at)}</p>
                </div>
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => versionsTarget && rollbackMut.mutate({ datasetId: versionsTarget.id, versionId: v.id })}
                  disabled={rollbackMut.isPending}
                >
                  Roll back
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Modal>

      {/* Validation errors */}
      <Modal
        isOpen={!!validationReport}
        onClose={() => { setValidationReport(null); setValidationAction(null) }}
        title="Validation errors"
      >
        {validationReport && <ValidationReportPanel report={validationReport} />}
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="ghost" onClick={() => { setValidationReport(null); setValidationAction(null) }}>Cancel</Button>
          <Button
            onClick={() => validationAction?.().then(() => {
              setValidationReport(null)
              setValidationAction(null)
            })}
          >
            Skip invalid rows
          </Button>
        </div>
      </Modal>
    </div>
  )
}
