// Spec 10 — Discovery option catalogs (genre tiles, sort, chip editors).
import type { ConstraintCategory, SortOption } from '../../../../types/search'

/** Spec 10 §17 — ~12 genre tiles covering the common CIP top-level groupings.
 *  Each tile drops a `major` scope chip whose value feeds the FTS query. */
export const GENRE_TILES: { value: string; label: string }[] = [
  { value: 'computer science', label: 'Computer Science' },
  { value: 'data science', label: 'Data Science' },
  { value: 'business', label: 'Business' },
  { value: 'engineering', label: 'Engineering' },
  { value: 'nursing', label: 'Health & Nursing' },
  { value: 'public policy', label: 'Public Policy' },
  { value: 'law', label: 'Law' },
  { value: 'education', label: 'Education' },
  { value: 'psychology', label: 'Psychology' },
  { value: 'economics', label: 'Economics' },
  { value: 'design', label: 'Arts & Design' },
  { value: 'biology', label: 'Natural Sciences' },
]

/** Spec 10 §6 — sort options. */
export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'fitness', label: 'Fitness score' },
  { value: 'confidence', label: 'Confidence score' },
  { value: 'tuition_asc', label: 'Tuition (low to high)' },
  { value: 'tuition_desc', label: 'Tuition (high to low)' },
  { value: 'acceptance_asc', label: 'Acceptance rate (low to high)' },
  { value: 'acceptance_desc', label: 'Acceptance rate (high to low)' },
  { value: 'salary_desc', label: 'Best outcomes (salary)' },
  { value: 'employment_desc', label: 'Best job placement' },
  { value: 'deadline', label: 'Deadline (earliest)' },
  { value: 'recently_added', label: 'Recently added' },
]

export const DEGREE_OPTIONS: { value: string; label: string }[] = [
  { value: 'bachelors', label: "Bachelor's" },
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'PhD' },
  { value: 'doctorate', label: 'Doctorate' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'associate', label: 'Associate' },
  { value: 'professional', label: 'Professional' },
]

export const FORMAT_OPTIONS: { value: string; label: string }[] = [
  { value: 'in_person', label: 'In-person' },
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
]

export const SELECTIVITY_OPTIONS: { value: string; label: string }[] = [
  { value: 'low', label: 'Less selective' },
  { value: 'medium', label: 'Moderately selective' },
  { value: 'high', label: 'Selective' },
  { value: 'very_high', label: 'Highly selective' },
]

/** Spec 10 §5 — campus setting facet. */
export const CAMPUS_SETTING_OPTIONS: { value: string; label: string }[] = [
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
]

export const SEASON_OPTIONS: { value: string; label: string }[] = [
  { value: 'fall', label: 'Fall' },
  { value: 'spring', label: 'Spring' },
  { value: 'summer', label: 'Summer' },
  { value: 'winter', label: 'Winter' },
]

/** Short chip label per category (the "Category" half of `Category · Value`). */
export const CATEGORY_LABELS: Record<ConstraintCategory, string> = {
  degree_level: 'Degree',
  major: 'Field',
  location: 'Location',
  budget: 'Budget',
  format: 'Format',
  start_term: 'Start',
  duration: 'Duration',
  selectivity: 'Selectivity',
  other: 'Note',
}

/** Categories offered in the "+ Add" / Filters menu, in display order. */
export const ADDABLE_CATEGORIES: ConstraintCategory[] = [
  'degree_level',
  'major',
  'location',
  'budget',
  'format',
  'duration',
  'selectivity',
  'start_term',
  'other',
]
