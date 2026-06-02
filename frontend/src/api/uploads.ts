// Spec 54 §2/§13 — direct-to-storage uploads, kept out of pages/.
//
// A presigned upload URL is an *external* object-storage endpoint (S3), NOT our
// API — so it must bypass the `apiClient` axios instance (no bearer token, no
// /api/v1 baseURL) and use the native fetch. Centralizing it here keeps the §13
// rule honest: pages call a typed `api/` function, never a raw `fetch()`.
//
// The two-step contract: a typed `api/` call mints the presigned URL (e.g.
// `requestPostMediaUpload`, `initDatasetUpload`), then the bytes go straight to
// storage via the PUT below.

/**
 * PUT a file's bytes to a presigned storage URL.
 *
 * Pure transport: returns the raw `Response` (callers decide how to surface
 * failure), matching the prior in-page behavior exactly.
 */
export function putFileToPresignedUrl(
  url: string,
  file: File | Blob,
  contentType?: string,
): Promise<Response> {
  const type = contentType ?? (file as File).type ?? 'application/octet-stream'
  return fetch(url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': type },
  })
}
