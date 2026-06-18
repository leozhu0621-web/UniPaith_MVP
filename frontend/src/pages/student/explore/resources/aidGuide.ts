// Financial-aid reference guide (Spec 2026-06-14 §Financial). Authored general
// knowledge — how college aid works — with NO invented amounts or deadlines.
// The per-program dollar figures live on the real cost-comparison surface; this
// is the "how it works" explainer that pairs with it.
import { Landmark, Award, GraduationCap, Banknote, Briefcase, Globe2 } from 'lucide-react'
import type { GuideSection } from './guideTypes'

export const AID_GUIDE: GuideSection[] = [
  {
    id: 'need-based',
    icon: Landmark,
    heading: 'Need-based aid',
    body: 'Need-based aid is awarded on what your family can afford rather than on grades. In the US it starts with two forms.',
    bullets: [
      'FAFSA — the federal form for US citizens and eligible non-citizens; it determines your eligibility for federal grants, work-study, and loans.',
      'CSS Profile — an additional form many private colleges use to award their own institutional aid.',
      'Both produce a figure schools use to estimate what your family can pay; the school then builds an aid package toward the rest.',
    ],
  },
  {
    id: 'scholarships',
    icon: Award,
    heading: 'Merit & external scholarships',
    body: 'Scholarships are gift aid (no repayment) awarded for achievement or a specific profile.',
    bullets: [
      'Institutional merit awards come from the school itself — often automatic with your application, sometimes a separate essay.',
      'External scholarships come from foundations, employers, and community groups; they are competitive and deadline-driven, so start early.',
      'Treat scholarship search as ongoing — many have one fixed deadline a year.',
    ],
  },
  {
    id: 'grants',
    icon: GraduationCap,
    heading: 'Grants',
    body: 'Grants are gift aid you do not repay, usually need-based.',
    bullets: [
      'Federal grants (such as the Pell Grant) go to students with demonstrated need who file the FAFSA.',
      'Many states run their own grant programs for residents attending in-state schools.',
      'Gift aid (grants + scholarships) is always better than loans — chase it first.',
    ],
  },
  {
    id: 'loans',
    icon: Banknote,
    heading: 'Loans',
    body: 'Loans are borrowed money you repay with interest. Borrow conservatively — only after gift aid.',
    bullets: [
      'Federal student loans (subsidized and unsubsidized) generally offer better terms and protections than private loans.',
      'Private loans come from banks and lenders and often require a cosigner; compare the rate and terms carefully.',
      'A rule of thumb: avoid borrowing more in total than you expect to earn in your first year after graduating.',
    ],
  },
  {
    id: 'work',
    icon: Briefcase,
    heading: 'Work-study & assistantships',
    body: 'Earning while you study reduces what you need to borrow.',
    bullets: [
      'Federal work-study funds part-time, often on-campus jobs for students with need.',
      'For graduate study, teaching and research assistantships (TA/RA) frequently cover tuition plus a stipend.',
    ],
  },
  {
    id: 'international',
    icon: Globe2,
    heading: 'If you are an international student',
    body: 'Most US federal aid (FAFSA-based grants, loans, and work-study) is not open to non-citizens — but other paths remain.',
    bullets: [
      'Institutional aid — some schools award need-based or merit aid to international students; check each school’s policy.',
      'External scholarships open to your nationality or field.',
      'Private loans usually require a US-based cosigner; a few lenders serve international students without one.',
      'See the International tab for visa, work-authorization, and proof-of-finances details.',
    ],
  },
]

// Shown once at the top of the guide — keeps it honest as general reference.
export const AID_GUIDE_DISCLAIMER =
  'General guidance, not personalized advice. Exact amounts, eligibility, and deadlines vary — confirm them with each school’s financial-aid office.'
