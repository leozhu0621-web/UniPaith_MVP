import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DocumentsTab from '../pages/student/myspace/prep/DocumentsTab'

vi.mock('../api/documents', () => ({
  deleteDocument: vi.fn(),
  listDocuments: vi.fn(),
}))

vi.mock('../pages/student/profile/FileDropzone', () => ({
  default: ({ label }: { label: string }) => <div data-testid="dropzone">{label}</div>,
}))

vi.mock('../stores/confirm-store', () => ({
  confirmDialog: vi.fn(),
}))

vi.mock('../stores/toast-store', () => ({
  showToast: vi.fn(),
}))

import { listDocuments } from '../api/documents'

function renderDocumentsTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <DocumentsTab />
    </QueryClientProvider>,
  )
}

describe('DocumentsTab materials ledger', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('surfaces missing core files, material arrivals, and upload target changes', async () => {
    vi.mocked(listDocuments).mockResolvedValue([
      {
        id: 'doc-1',
        student_id: 'student-1',
        document_type: 'transcript',
        file_name: 'fall-transcript.pdf',
        file_size_bytes: 2048,
        mime_type: 'application/pdf',
        uploaded_at: '2026-05-01T12:00:00Z',
        verification_status: 'verified',
      },
      {
        id: 'doc-2',
        student_id: 'student-1',
        document_type: 'portfolio',
        file_name: 'research-portfolio.pdf',
        file_size_bytes: 4096,
        mime_type: 'application/pdf',
        uploaded_at: '2026-06-10T12:00:00Z',
        verification_status: null,
      },
    ])

    renderDocumentsTab()

    expect(await screen.findByRole('region', { name: /materials ledger/i })).toBeTruthy()
    expect(screen.getByText('1/2 core files')).toBeTruthy()
    expect(screen.getByText('Missing Resume.')).toBeTruthy()
    expect(screen.getByText('2 types')).toBeTruthy()
    expect(screen.getByText('1/2 verified')).toBeTruthy()
    expect(screen.getByText('research-portfolio.pdf')).toBeTruthy()
    expect(screen.getByText('fall-transcript.pdf')).toBeTruthy()
    expect(screen.getByText('verified')).toBeTruthy()
    expect(screen.getByText('recorded')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /Upload resume/i }))

    expect(screen.getByTestId('dropzone').textContent).toBe('Upload a resume')
  })
})
