import { useEffect } from 'react'

// Sets the document <title> per route so each page's title matches its purpose
// (Spec/04 §15). Pass a short page label; "· UniPaith" is appended.
export function useDocumentTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} · UniPaith` : 'UniPaith'
  }, [title])
}
