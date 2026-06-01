import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { UploadCloud, Save, FileSpreadsheet, ArrowRight, ArrowLeft } from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Badge from '../../../components/ui/Badge'
import { showToast } from '../../../stores/toast-store'
import type { DatasetType, DatasetInspect, DatasetValidationReport } from '../../../types'
import {
  uploadDatasetFile, inspectDatasetFile, validateDatasetFile, confirmDatasetUpload,
  getMappingTemplates, createMappingTemplate,
} from '../../../api/institutions'
import {
  DATASET_TYPES, USAGE_SCOPES, PLATFORM_FIELDS, REQUIRED_FIELDS, PROGRAM_FIELD, autoMap,
} from './constants'
import ValidationReportView from './ValidationReportView'

interface Props {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

export default function UploadWizard({ isOpen, onClose, onComplete }: Props) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState(0)

  // step 1 — details
  const [name, setName] = useState('')
  const [type, setType] = useState<DatasetType>('prospect_list')
  const [description, setDescription] = useState('')
  const [coverageStart, setCoverageStart] = useState('')
  const [coverageEnd, setCoverageEnd] = useState('')

  // step 2 — file
  const [file, setFile] = useState<File | null>(null)
  const [fileRef, setFileRef] = useState('')
  const [uploading, setUploading] = useState(false)
  const [inspect, setInspect] = useState<DatasetInspect | null>(null)

  // step 3 — mapping
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [templateName, setTemplateName] = useState('')

  // step 4/5 — validation + normalization
  const [validation, setValidation] = useState<DatasetValidationReport | null>(null)
  const [normalization, setNormalization] = useState<Record<string, string>>({})
  const [validating, setValidating] = useState(false)

  // step 6 — scope + submit
  const [usageScope, setUsageScope] = useState('all')
  const [submitting, setSubmitting] = useState(false)

  const hasProgramField = !!PROGRAM_FIELD[type]
  const steps = useMemo(
    () => ['Details', 'File', 'Map columns', ...(hasProgramField ? ['Normalize'] : []), 'Validate', 'Usage'],
    [hasProgramField],
  )
  const current = steps[step]

  const templatesQ = useQuery({
    queryKey: ['mapping-templates', type],
    queryFn: () => getMappingTemplates(type),
    enabled: isOpen,
  })

  function reset() {
    setStep(0); setName(''); setType('prospect_list'); setDescription('')
    setCoverageStart(''); setCoverageEnd(''); setFile(null); setFileRef(''); setInspect(null)
    setMapping({}); setTemplateName(''); setValidation(null); setNormalization({})
    setUsageScope('all')
  }
  function close() { reset(); onClose() }

  async function handleFile(f: File) {
    setFile(f)
    setUploading(true)
    try {
      const { file_ref } = await uploadDatasetFile(f)
      setFileRef(file_ref)
      const insp = await inspectDatasetFile(file_ref)
      setInspect(insp)
      setMapping(autoMap(insp.columns, PLATFORM_FIELDS[type]))
    } catch {
      showToast('Could not read that file. Use CSV, TSV, or xlsx.', 'error')
      setFile(null)
    } finally {
      setUploading(false)
    }
  }

  async function runValidation(): Promise<boolean> {
    if (!fileRef) return false
    setValidating(true)
    try {
      const res = await validateDatasetFile({ dataset_type: type, mapping, file_ref: fileRef })
      setValidation(res.validation_report)
      setNormalization(res.normalization_map)
      return true
    } catch {
      showToast('Validation failed — check your column mapping.', 'error')
      return false
    } finally {
      setValidating(false)
    }
  }

  async function next() {
    if (current === 'Details') {
      if (!name.trim()) { showToast('Give the dataset a name.', 'warning'); return }
      setStep(step + 1)
    } else if (current === 'File') {
      if (!fileRef || !inspect) { showToast('Choose a file first.', 'warning'); return }
      setStep(step + 1)
    } else if (current === 'Map columns') {
      const required = REQUIRED_FIELDS[type]
      const mapped = new Set(Object.values(mapping))
      const missing = required.filter((f) => !mapped.has(f))
      if (missing.length) { showToast(`Map a column to: ${missing.join(', ')}`, 'warning'); return }
      const ok = await runValidation()
      if (ok) setStep(step + 1)
    } else if (current === 'Normalize' || current === 'Validate') {
      setStep(step + 1)
    }
  }
  function back() { if (step > 0) setStep(step - 1) }

  async function submit() {
    if (!fileRef || !file) return
    setSubmitting(true)
    try {
      await confirmDatasetUpload({
        name: name.trim(),
        dataset_type: type,
        file_ref: fileRef,
        file_name: file.name,
        mapping,
        description: description || undefined,
        usage_scope: usageScope,
        coverage_start: coverageStart || null,
        coverage_end: coverageEnd || null,
        file_size_bytes: file.size,
      })
      showToast('Dataset created.', 'success')
      onComplete()
      close()
    } catch {
      showToast('Could not create the dataset.', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  async function saveTemplate() {
    if (!templateName.trim()) { showToast('Name the template.', 'warning'); return }
    try {
      await createMappingTemplate({ name: templateName.trim(), dataset_type: type, column_mapping: mapping })
      showToast('Mapping template saved.', 'success')
      setTemplateName('')
      templatesQ.refetch()
    } catch {
      showToast('Could not save template.', 'error')
    }
  }

  function applyTemplate(columnMapping: Record<string, string>) {
    // keep only columns present in the current file
    const cols = new Set(inspect?.columns ?? [])
    const next: Record<string, string> = {}
    for (const [col, field] of Object.entries(columnMapping)) if (cols.has(col)) next[col] = field
    setMapping(next)
    showToast('Template applied.', 'success')
  }

  const progress = Math.round(((step + 1) / steps.length) * 100)

  const footer = (
    <div className="flex w-full items-center justify-between">
      <Button variant="ghost" onClick={current === 'Details' ? close : back} disabled={submitting}>
        {current === 'Details' ? 'Cancel' : (<><ArrowLeft size={14} /> Back</>)}
      </Button>
      {current === 'Usage' ? (
        <Button variant="secondary" onClick={submit} loading={submitting}>Create dataset</Button>
      ) : (
        <Button variant="secondary" onClick={next} loading={uploading || validating}>
          {current === 'Validate' && validation && validation.valid_rows < validation.total_rows
            ? 'Skip invalid rows & continue'
            : 'Continue'}{' '}
          <ArrowRight size={14} />
        </Button>
      )}
    </div>
  )

  return (
    <Modal isOpen={isOpen} onClose={close} title="Upload dataset" size="lg" footer={footer}>
      {/* progress */}
      <div className="mb-4">
        <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
          <span>{current} · step {step + 1} of {steps.length}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-muted">
          <div className="h-1.5 rounded-full bg-secondary transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="min-h-[18rem]">
        {current === 'Details' && (
          <div className="space-y-3">
            <Input label="Dataset name" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Admissions history 2020–2024" required />
            <Select label="Type" value={type} onChange={(e) => setType(e.target.value as DatasetType)}
              options={DATASET_TYPES.map((t) => ({ value: t.value, label: t.label }))} />
            <p className="-mt-1 text-xs text-muted-foreground">
              {DATASET_TYPES.find((t) => t.value === type)?.blurb}
            </p>
            <Textarea label="Description (optional)" value={description} rows={2}
              onChange={(e) => setDescription(e.target.value)} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Coverage start" type="date" value={coverageStart}
                onChange={(e) => setCoverageStart(e.target.value)} />
              <Input label="Coverage end" type="date" value={coverageEnd}
                onChange={(e) => setCoverageEnd(e.target.value)} />
            </div>
          </div>
        )}

        {current === 'File' && (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border py-10 text-muted-foreground transition-colors hover:border-secondary hover:text-secondary"
            >
              <UploadCloud size={28} />
              <span className="text-sm font-medium">{file ? file.name : 'Choose a CSV, TSV, or xlsx file'}</span>
              {uploading && <span className="text-xs">Uploading…</span>}
            </button>
            <input ref={fileInput} type="file" accept=".csv,.tsv,.xlsx,.xlsm" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
            {inspect && (
              <div className="rounded-md border border-border p-3">
                <p className="mb-2 flex items-center gap-2 text-xs text-foreground">
                  <FileSpreadsheet size={14} className="text-secondary" />
                  {inspect.total_rows.toLocaleString()} rows · {inspect.columns.length} columns detected
                </p>
                <div className="flex flex-wrap gap-1">
                  {inspect.columns.map((c) => <Badge key={c} variant="neutral">{c}</Badge>)}
                </div>
              </div>
            )}
          </div>
        )}

        {current === 'Map columns' && inspect && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Map your columns to platform fields. Required: {REQUIRED_FIELDS[type].join(', ')}. Unmapped columns are ignored.
            </p>
            {(templatesQ.data?.length ?? 0) > 0 && (
              <div className="flex flex-wrap items-center gap-2 rounded-md bg-muted/60 p-2">
                <span className="text-xs text-muted-foreground">Load template:</span>
                {templatesQ.data!.map((t) => (
                  <button key={t.id} type="button" onClick={() => applyTemplate(t.column_mapping)}
                    className="rounded border border-border bg-background px-2 py-0.5 text-xs hover:border-secondary">
                    {t.name}
                  </button>
                ))}
              </div>
            )}
            <div className="max-h-60 space-y-1.5 overflow-y-auto pr-1">
              {inspect.columns.map((col) => (
                <div key={col} className="flex items-center gap-2">
                  <span className="w-40 shrink-0 truncate font-mono text-xs text-foreground" title={col}>{col}</span>
                  <span className="text-muted-foreground">→</span>
                  <select
                    value={mapping[col] || ''}
                    onChange={(e) => setMapping((m) => ({ ...m, [col]: e.target.value }))}
                    className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
                  >
                    <option value="">— skip —</option>
                    {PLATFORM_FIELDS[type].map((f) => (
                      <option key={f} value={f}>
                        {f}{REQUIRED_FIELDS[type].includes(f) ? ' *' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 border-t border-border pt-2">
              <Input value={templateName} onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Save this mapping as a template…" />
              <Button variant="tertiary" size="sm" onClick={saveTemplate}><Save size={14} /> Save</Button>
            </div>
          </div>
        )}

        {current === 'Normalize' && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">Program normalization</p>
            <p className="text-xs text-muted-foreground">
              Your program names are matched to UniPaith program records.
            </p>
            <div className="rounded-md border border-border p-3 text-xs">
              <p className="mb-1 text-success">
                {Object.keys(normalization).length} program{Object.keys(normalization).length === 1 ? '' : 's'} matched
              </p>
              {Object.keys(normalization).slice(0, 8).map((k) => (
                <div key={k} className="text-muted-foreground">• {k}</div>
              ))}
              {(validation?.unmappable_programs.length ?? 0) > 0 && (
                <p className="mt-2 text-warning">
                  {validation!.unmappable_programs.length} program value(s) didn’t match — see the next step.
                </p>
              )}
            </div>
          </div>
        )}

        {current === 'Validate' && validation && (
          <div className="space-y-3">
            <ValidationReportView report={validation} />
            {validation.valid_rows < validation.total_rows && (
              <p className="text-xs text-muted-foreground">
                You can skip the flagged rows and continue, or go back to fix your mapping.
              </p>
            )}
          </div>
        )}

        {current === 'Usage' && (
          <div className="space-y-3">
            <Select label="Usage scope" value={usageScope} onChange={(e) => setUsageScope(e.target.value)}
              options={USAGE_SCOPES} />
            <p className="-mt-1 text-xs text-muted-foreground">
              Controls where this dataset can be used. A marketing-only dataset never feeds matching.
            </p>
            <div className="rounded-md border border-border bg-muted/40 p-3 text-xs text-foreground">
              <p className="font-medium">{name}</p>
              <p className="text-muted-foreground">
                {DATASET_TYPES.find((t) => t.value === type)?.label} · {inspect?.total_rows.toLocaleString()} rows
                {validation ? ` · ${validation.valid_rows} valid` : ''}
              </p>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
