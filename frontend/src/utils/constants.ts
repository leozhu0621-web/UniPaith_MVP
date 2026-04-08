export const COMPETITION_LEVELS = [
  { value: 'school', label: 'School' },
  { value: 'state', label: 'State / Regional' },
  { value: 'national', label: 'National' },
  { value: 'international', label: 'International' },
]

export const WORK_EXPERIENCE_TYPES = [
  { value: 'employment', label: 'Employment' },
  { value: 'internship', label: 'Internship' },
  { value: 'volunteering', label: 'Volunteering' },
  { value: 'service', label: 'Community Service' },
]

export const COMPENSATION_TYPES = [
  { value: 'paid', label: 'Paid' },
  { value: 'unpaid', label: 'Unpaid' },
  { value: 'stipend', label: 'Stipend' },
]

export const DEGREE_LABELS: Record<string, string> = {
  bachelors: 'B.S.',
  masters: 'M.S.',
  phd: 'Ph.D.',
  certificate: 'Certificate',
  diploma: 'Diploma',
  high_school: 'High School',
  associate: 'Associate',
}

export const TEST_TYPES = [
  'SAT', 'GRE', 'GMAT', 'TOEFL', 'IELTS', 'AP', 'IB', 'ACT', 'LSAT', 'MCAT', 'DUOLINGO',
] as const

export const ACTIVITY_TYPES = [
  { value: 'work_experience', label: 'Work Experience' },
  { value: 'research', label: 'Research' },
  { value: 'volunteering', label: 'Volunteering' },
  { value: 'extracurricular', label: 'Extracurricular' },
  { value: 'leadership', label: 'Leadership' },
  { value: 'awards', label: 'Awards' },
  { value: 'publications', label: 'Publications' },
]

export const STATUS_COLORS: Record<string, string> = {
  draft: 'neutral',
  submitted: 'info',
  under_review: 'warning',
  interview: 'info',
  decision_made: 'warning',
  admitted: 'success',
  rejected: 'danger',
  waitlisted: 'warning',
  deferred: 'warning',
  published: 'success',
  completed: 'success',
  cancelled: 'neutral',
  confirmed: 'success',
  invited: 'info',
  scheduling: 'info',
  no_show: 'danger',
  open: 'success',
  awaiting_response: 'warning',
  resolved: 'neutral',
  closed: 'neutral',
}

export const TIER_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Reach', color: 'danger' },
  2: { label: 'Match', color: 'warning' },
  3: { label: 'Safety', color: 'success' },
}

export const INSTITUTION_TYPES = [
  { value: 'university', label: 'University' },
  { value: 'college', label: 'College' },
  { value: 'technical_institute', label: 'Technical Institute' },
  { value: 'community_college', label: 'Community College' },
]

export const DELIVERY_FORMAT_LABELS: Record<string, string> = {
  in_person: 'In Person',
  online: 'Online',
  hybrid: 'Hybrid',
}

export const CAMPUS_SETTING_LABELS: Record<string, string> = {
  urban: 'Urban',
  suburban: 'Suburban',
  rural: 'Rural',
}

export const EVENT_TYPES = [
  { value: 'webinar', label: 'Webinar' },
  { value: 'campus_visit', label: 'Campus Visit' },
  { value: 'info_session', label: 'Info Session' },
  { value: 'workshop', label: 'Workshop' },
]

export const INTERVIEW_TYPES = [
  { value: 'video', label: 'Video' },
  { value: 'in_person', label: 'In Person' },
  { value: 'phone', label: 'Phone' },
  { value: 'group', label: 'Group' },
]

export const DECISION_OPTIONS = [
  { value: 'admitted', label: 'Admit' },
  { value: 'rejected', label: 'Reject' },
  { value: 'waitlisted', label: 'Waitlist' },
  { value: 'deferred', label: 'Defer' },
]

export const CITY_SIZE_OPTIONS = [
  { value: 'big_city', label: 'Big City' },
  { value: 'college_town', label: 'College Town' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
  { value: 'no_preference', label: 'No Preference' },
]

export const FUNDING_OPTIONS = [
  { value: 'full_scholarship', label: 'Full Scholarship' },
  { value: 'partial', label: 'Partial Scholarship' },
  { value: 'self_funded', label: 'Self-Funded' },
  { value: 'flexible', label: 'Flexible' },
]

export const GPA_SCALES = [
  { value: '4.0', label: '4.0 Scale' },
  { value: 'percentage', label: 'Percentage' },
  { value: 'ib', label: 'IB (45)' },
  { value: '10.0', label: '10.0 Scale' },
]

export const PLATFORM_TYPES = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'github', label: 'GitHub' },
  { value: 'personal_site', label: 'Personal Website' },
  { value: 'portfolio', label: 'Portfolio' },
  { value: 'wechat', label: 'WeChat' },
  { value: 'twitter', label: 'Twitter/X' },
  { value: 'other', label: 'Other' },
]

export const PROFICIENCY_LEVELS = [
  { value: 'native', label: 'Native' },
  { value: 'fluent', label: 'Fluent' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'beginner', label: 'Beginner' },
]

export const LANGUAGE_CERT_TYPES = [
  { value: 'TOEFL', label: 'TOEFL' },
  { value: 'IELTS', label: 'IELTS' },
  { value: 'DELF', label: 'DELF/DALF' },
  { value: 'HSK', label: 'HSK' },
  { value: 'JLPT', label: 'JLPT' },
  { value: 'TOPIK', label: 'TOPIK' },
  { value: 'other', label: 'Other' },
]

export const RESEARCH_ROLES = [
  { value: 'assistant', label: 'Research Assistant' },
  { value: 'independent', label: 'Independent Researcher' },
  { value: 'lead', label: 'Lead Researcher' },
]

export const RESEARCH_OUTPUTS = [
  { value: 'paper', label: 'Paper' },
  { value: 'poster', label: 'Poster' },
  { value: 'code', label: 'Code' },
  { value: 'none', label: 'None yet' },
]

export const PORTFOLIO_ITEM_TYPES = [
  { value: 'project', label: 'Project' },
  { value: 'writing_sample', label: 'Writing Sample' },
  { value: 'artwork', label: 'Artwork' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'code', label: 'Code / Repository' },
  { value: 'other', label: 'Other' },
]

export const DOCUMENT_TYPES = [
  { value: 'transcript', label: 'Transcript' },
  { value: 'essay', label: 'Essay' },
  { value: 'resume', label: 'Resume' },
  { value: 'recommendation', label: 'Recommendation' },
  { value: 'portfolio', label: 'Portfolio' },
  { value: 'certificate', label: 'Certificate' },
]
