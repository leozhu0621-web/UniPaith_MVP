import { lazy, Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { FileText, FolderOpen, GraduationCap, MessageCircleQuestion, NotebookPen, UserCheck } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import { listDocuments } from '../../../api/documents'
import { listRecommendations } from '../../../api/recommendations'
import { listWorkshopRuns } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import usePageTitle from '../../../hooks/usePageTitle'
import FileDropzone from '../profile/FileDropzone'

const WorkshopsTab = lazy(() => import('../apply/WorkshopsTab'))
const PromptLibraryTab = lazy(() => import('../apply/promptlibrary/PromptLibraryTab'))
const RecommendationsPage = lazy(() => import('../RecommendationsPage'))
const InterviewPracticePanel = lazy(() => import('../apply/InterviewPracticePanel'))

type PrepTab = 'workshops' | 'prompts' | 'interviews' | 'recommenders' | 'documents'
type StudentDocument = {
  id?: string
  file_name?: string
  name?: string
  document_type?: string
  type?: string
  status?: string
}

const TABS: { key: PrepTab; label: string; icon: typeof GraduationCap }[] = [
  { key: 'workshops', label: 'Workshops', icon: GraduationCap },
  { key: 'prompts', label: 'Prompts', icon: NotebookPen },
  { key: 'interviews', label: 'Interviews', icon: MessageCircleQuestion },
  { key: 'recommenders', label: 'Recommenders', icon: UserCheck },
  { key: 'documents', label: 'Documents', icon: FolderOpen },
]

export default function PrepPage() {
  usePageTitle('My Space · Prep')
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const [tab, setTab] = useState<PrepTab>(isPrepTab(rawTab) ? rawTab : 'workshops')
  const runs = useQuery({ queryKey: ['workshop-runs', 'prep-header'], queryFn: () => listWorkshopRuns(), staleTime: 60_000 })
  const recs = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: 60_000 })
  const docs = useQuery({ queryKey: ['documents'], queryFn: listDocuments, staleTime: 60_000 })

  useEffect(() => {
    if (isPrepTab(rawTab) && rawTab !== tab) setTab(rawTab)
  }, [rawTab, tab])

  const switchTab = (next: PrepTab) => {
    setTab(next)
    const params = new URLSearchParams(searchParams)
    if (next === 'workshops') params.delete('tab')
    else params.set('tab', next)
    setSearchParams(params, { replace: true })
  }

  const runCount = Array.isArray(runs.data) ? runs.data.length : 0
  const recList = Array.isArray(recs.data) ? recs.data : []
  const docList: StudentDocument[] = Array.isArray(docs.data) ? docs.data : []
  const requestedRecs = recList.filter(rec => rec.status === 'requested').length
  const receivedRecs = recList.filter(rec => rec.status === 'received').length

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-5">
        <p className="up-eyebrow">My Space · Workspace</p>
        <h1 className="text-h1 text-foreground">Prepare without losing the thread</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Feedback, prompts, interview practice, recommenders, and documents are gathered here. Workshops remain feedback-only.
        </p>
      </header>

      <section className="mb-5 grid gap-3 md:grid-cols-3">
        <ReadinessCard label="Workshop feedback" value={runCount} detail="Essay, interview, and test runs" />
        <ReadinessCard label="Recommenders" value={`${receivedRecs}/${recList.length || 0}`} detail={requestedRecs ? `${requestedRecs} waiting on a response` : 'No pending requests'} />
        <ReadinessCard label="Documents" value={docList.length} detail="Uploaded evidence and application material" />
      </section>

      <div className="mb-5 overflow-x-auto border-b border-border no-scrollbar" role="tablist" aria-label="Preparation sections">
        <div className="flex w-max gap-1">
          {TABS.map(item => (
            <button
              key={item.key}
              role="tab"
              aria-selected={tab === item.key}
              onClick={() => switchTab(item.key)}
              className={`inline-flex min-h-11 items-center gap-1.5 border-b-2 px-4 text-sm font-semibold transition-colors ${
                tab === item.key
                  ? 'border-secondary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <item.icon size={15} />
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <Suspense fallback={<div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>}>
        {tab === 'workshops' && <WorkshopsTab />}
        {tab === 'prompts' && <PromptLibraryTab />}
        {tab === 'interviews' && (
          <Card className="p-5">
            <div className="mb-4">
              <h2 className="text-h3 text-foreground">Interview practice</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Practice or score a response. Feedback stays coaching-only; Uni never writes your answer.
              </p>
            </div>
            <InterviewPracticePanel />
          </Card>
        )}
        {tab === 'recommenders' && <RecommendationsPage />}
        {tab === 'documents' && <DocumentsWorkspace documents={docList} loading={docs.isLoading} />}
      </Suspense>
    </main>
  )
}

function isPrepTab(value: string | null): value is PrepTab {
  return Boolean(value && TABS.some(tab => tab.key === value))
}

function ReadinessCard({ label, value, detail }: { label: string; value: number | string; detail: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </Card>
  )
}

function DocumentsWorkspace({ documents, loading }: { documents: StudentDocument[]; loading: boolean }) {
  if (loading) return <div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>
  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
      <Card className="p-5">
        <h2 className="text-h3 text-foreground">Upload documents</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Add material once, then reuse it across applications and intake confirmation.
        </p>
        <div className="mt-4 space-y-3">
          <FileDropzone documentType="resume" label="Resume or CV" />
          <FileDropzone documentType="essay" label="Essay draft or writing sample" accept=".pdf,.doc,.docx,.txt" />
          <FileDropzone documentType="financial_doc" label="Financial aid or offer document" />
        </div>
      </Card>
      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-h3 text-foreground">Document library</h2>
            <p className="mt-1 text-sm text-muted-foreground">Uploaded files appear with processing status and source evidence.</p>
          </div>
          <Badge variant="neutral">{documents.length}</Badge>
        </div>
        {documents.length === 0 ? (
          <EmptyState
            icon={<FileText size={40} />}
            title="No documents yet"
            description="Upload a transcript, resume, essay draft, offer letter, or aid document to start building evidence."
          />
        ) : (
          <div className="space-y-2">
            {documents.map(doc => (
              <div key={doc.id ?? doc.file_name} className="flex items-center gap-3 rounded-md border border-border bg-background px-3 py-2">
                <FileText size={16} className="text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-foreground">{doc.file_name ?? doc.name ?? 'Document'}</p>
                  <p className="text-xs text-muted-foreground">{doc.document_type ?? doc.type ?? 'Uploaded material'} · {doc.status ?? 'processing'}</p>
                </div>
                <Badge variant={doc.status === 'processed' ? 'success' : 'neutral'}>{doc.status ?? 'uploaded'}</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
