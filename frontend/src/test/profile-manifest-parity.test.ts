// Profile manifest ↔ render parity (Phase 1 of the profile-standard system).
// Guarantees every REQUIRED manifest section is actually rendered on its detail
// page — so adding a section to the standard forces a render block to exist
// (and the whole fleet shows it). The manifest is the single source of truth
// (generated from the backend); this test is its render contract.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import manifest from '../generated/profile-manifest.json'

const PAGES: Record<string, string> = {
  institution: 'src/pages/student/institution/InstitutionDetail.tsx',
  school: 'src/pages/student/SchoolSubunitPage.tsx',
  program: 'src/pages/student/ProgramDetailPage.tsx',
}

// Each required section maps to a lowercase string that must appear in the page.
// Verified against the live MIT/Sloan/MBAn render. Add an entry when you add a
// required section to the manifest.
const ANCHORS: Record<string, string> = {
  'institution:identity': 'description',
  'institution:rankings': 'ranking',
  'institution:report_card': 'report card',
  'institution:admissions_funnel': 'admissions',
  'institution:campus_resources': 'campus resources',
  'institution:citation': 'source',
  'school:identity': 'website',
  'school:about_detail': 'leadership',
  'program:basics': 'length',
  'program:admissions': 'admissions',
  'program:costs': 'tuition',
  'program:outcomes': 'outcomes',
}

describe('profile manifest ↔ render parity', () => {
  for (const [level, sections] of Object.entries(manifest.levels as Record<string, any[]>)) {
    const src = readFileSync(PAGES[level], 'utf8').toLowerCase()
    for (const sec of sections) {
      if (!sec.required) continue
      const key = `${level}:${sec.id}`
      it(`${key} has a render anchor`, () => {
        const anchor = ANCHORS[key]
        expect(anchor, `no anchor mapped for required section ${key}`).toBeTruthy()
        expect(src.includes(anchor), `page ${PAGES[level]} is missing render for "${sec.id}" (anchor "${anchor}")`).toBe(true)
      })
    }
  }
})
