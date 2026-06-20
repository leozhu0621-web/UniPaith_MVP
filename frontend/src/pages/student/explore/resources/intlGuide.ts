// International-student reference guide (Spec 2026-06-14 §International). Authored
// general knowledge about studying in the US on a visa — NO fabricated rules or
// dates; immigration policy changes, so it points students to official sources.
import { Plane, FileText, MessagesSquare, ShieldCheck, Briefcase, Languages, Wallet } from 'lucide-react'
import type { GuideSection } from './guideTypes'

export const INTL_GUIDE: GuideSection[] = [
  {
    id: 'visa-types',
    icon: Plane,
    heading: 'Student visa types',
    body: 'Most degree-seeking international students study on one of two visas.',
    bullets: [
      'F-1 — the standard visa for academic study at an accredited US school.',
      'J-1 — an exchange-visitor visa used by some sponsored or exchange programs.',
      'Which one applies depends on your program and funding; the school’s international office confirms it.',
    ],
  },
  {
    id: 'i20',
    icon: FileText,
    heading: 'I-20 / DS-2019 and SEVIS',
    body: 'After you are admitted and show you can fund your studies, the school issues the document that lets you apply for a visa.',
    bullets: [
      'F-1 students receive a Form I-20; J-1 students receive a DS-2019.',
      'You pay the SEVIS fee and use this document to book your visa interview.',
      'Keep it current — it must be updated if your program, funding, or dates change.',
    ],
  },
  {
    id: 'interview',
    icon: MessagesSquare,
    heading: 'The visa interview',
    body: 'You apply at a US embassy or consulate in your country and attend an interview.',
    bullets: [
      'Be ready to show proof of admission, finances, and ties to home.',
      'Wait times vary widely by country — schedule as early as you can after you get your I-20/DS-2019.',
    ],
  },
  {
    id: 'maintain',
    icon: ShieldCheck,
    heading: 'Maintaining status',
    body: 'Your visa stays valid only while you follow its rules.',
    bullets: [
      'Enroll full-time each term and make normal progress toward your degree.',
      'On-campus work is generally limited; off-campus work needs authorization first.',
      'Talk to your international office before dropping below full-time, taking leave, or traveling.',
    ],
  },
  {
    id: 'work',
    icon: Briefcase,
    heading: 'Working and post-study options',
    body: 'F-1 students can often work in their field with prior authorization.',
    bullets: [
      'CPT — curricular practical training, for work that is part of your program (e.g. an internship).',
      'OPT — optional practical training, up to a year of work in your field after (or sometimes during) study.',
      'STEM OPT — eligible STEM graduates may extend OPT. Apply through your international office; timing matters.',
    ],
  },
  {
    id: 'english',
    icon: Languages,
    heading: 'English proficiency',
    body: 'Most programs require proof of English unless you qualify for a waiver.',
    bullets: [
      'Common tests: TOEFL, IELTS, and the Duolingo English Test — each program sets its own minimum scores.',
      'Waivers are common if your prior degree was taught in English or you are from a designated English-speaking country.',
      'Add your test score in Profile so we can match it against program requirements.',
    ],
  },
  {
    id: 'finances',
    icon: Wallet,
    heading: 'Proof of finances',
    body: 'Before issuing your I-20/DS-2019, schools require evidence you can fund your first year.',
    bullets: [
      'Bank statements, a sponsor’s affidavit, or a scholarship/assistantship letter are typical.',
      'The required amount is the school’s estimated cost of attendance — confirm the figure with the school.',
    ],
  },
]

export const INTL_GUIDE_DISCLAIMER =
  'General guidance — immigration rules change. Always confirm current requirements with your school’s international office and official government sources.'
