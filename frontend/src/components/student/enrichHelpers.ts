/** Helpers for the enrich widget — kept out of the component file so
 * react-refresh (fast refresh only with component-only exports) stays happy. */

const SPECIAL_LABELS: Record<string, string> = {
  gpa: 'GPA',
  date_of_birth: 'Date of birth',
  target_degree_level: 'Target degree level',
  field_of_interest: 'Field of interest',
}

export function humanizeField(field: string): string {
  if (SPECIAL_LABELS[field]) return SPECIAL_LABELS[field]
  return field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export const ACTION_PROMPT: Record<string, string> = {
  ask: 'Add this to sharpen your matches',
  confirm: 'Quick check — is this right?',
}
