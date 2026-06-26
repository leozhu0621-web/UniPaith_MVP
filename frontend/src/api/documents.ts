import apiClient from './client'
import axios from 'axios'
import { toArrayData } from './normalize'

export const requestUpload = (data: { document_type: string; file_name: string; content_type: string; file_size_bytes: number }) =>
  apiClient.post('/students/me/documents/request-upload', data).then(r => r.data)

export const confirmUpload = (docId: string) =>
  apiClient.post(`/students/me/documents/${docId}/confirm`).then(r => r.data)

export const listDocuments = () =>
  apiClient.get('/students/me/documents').then(r => toArrayData<any>(r.data))

export const getDocument = (docId: string) =>
  apiClient.get(`/students/me/documents/${docId}`).then(r => r.data)

export const deleteDocument = (docId: string) =>
  apiClient.delete(`/students/me/documents/${docId}`)

export const uploadToS3 = (url: string, file: File, onProgress?: (pct: number) => void) =>
  axios.put(url, file, {
    // Must match the Content-Type the presigned URL was signed with (callers use
    // `file.type || 'application/octet-stream'`). Without the same fallback, files
    // with an empty MIME type (.md, some .csv, drag-drops) get a 403
    // SignatureDoesNotMatch and the upload silently fails.
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
