/**
 * CampaignAudienceCopySuggester fallback (Spec 25 §10, 45 §16).
 * Rule-based drafts until the LLM agent is wired.
 */

export type DraftCopyInput = {
  objective: string
  ctaType: string
  campaignName: string
  institutionName?: string
  programName?: string
}

export type DraftCopyResult = {
  subject: string
  body: string
  alternateSubjects: string[]
  previewText: string
}

const TEMPLATES: Record<string, { subject: string; body: string; alternates: string[] }> = {
  application_open: {
    subject: 'Applications are open at {{institution_name}}',
    body: `Hi {{first_name}},

{{institution_name}} has opened applications for {{program_name}}. If you have been exploring options, this is a good time to review requirements and start your application.

{{program_name}} — learn more and apply when you are ready.

Best,
Admissions Team`,
    alternates: ['Ready to apply to {{program_name}}?', 'Your next step: {{program_name}} applications'],
  },
  event_promotion: {
    subject: 'You are invited — upcoming event at {{institution_name}}',
    body: `Hi {{first_name}},

We would like you to join us for an upcoming session about {{program_name}}. Reserve your spot using {{event_link}}.

We look forward to meeting you.

{{institution_name}}`,
    alternates: ['Join us for a {{program_name}} info session', 'Save your seat — {{institution_name}} event'],
  },
  scholarship_announcement: {
    subject: 'Scholarship update for {{program_name}}',
    body: `Hi {{first_name}},

{{institution_name}} has shared new scholarship information related to {{program_name}}. Review details on our program page and reach out if you have questions.

Best regards,
Financial Aid & Admissions`,
    alternates: ['New funding opportunities at {{institution_name}}'],
  },
  deadline_reminder: {
    subject: 'Reminder: key deadline approaching for {{program_name}}',
    body: `Hi {{first_name}},

This is a friendly reminder that an important deadline for {{program_name}} at {{institution_name}} is approaching. Please complete any outstanding steps in your application checklist.

Thank you,
Admissions Team`,
    alternates: ['Don’t miss the {{program_name}} deadline', 'Action needed: {{program_name}} timeline'],
  },
  nurture: {
    subject: 'Continuing your journey with {{institution_name}}',
    body: `Hi {{first_name}},

We noticed your interest in {{program_name}} and wanted to share a few resources that may help as you compare options. Visit our program page when you are ready to take the next step.

Warm regards,
{{institution_name}}`,
    alternates: ['Resources for your {{program_name}} search'],
  },
  general: {
    subject: '{{campaign_name}} — from {{institution_name}}',
    body: `Hi {{first_name}},

{{institution_name}} has an update we thought would be relevant as you explore {{program_name}}.

If you have questions, reply to this message or visit our program page.

Best,
Admissions Team`,
    alternates: ['An update from {{institution_name}}'],
  },
}

const CTA_CLOSERS: Record<string, string> = {
  learn_more: 'Learn more on our program page when you are ready.',
  rsvp_event: 'RSVP using the event link above to save your seat.',
  request_info: 'Reply or use our inquiry form if you would like more information.',
  start_application: 'When you are ready, start your application from the program page.',
}

export function draftCampaignCopy(input: DraftCopyInput): DraftCopyResult {
  const tpl = TEMPLATES[input.objective] ?? TEMPLATES.general
  const inst = input.institutionName ?? '{{institution_name}}'
  const prog = input.programName ?? '{{program_name}}'
  const name = input.campaignName.trim() || 'Outreach update'

  const fill = (s: string) =>
    s
      .replace(/\{\{institution_name\}\}/g, inst)
      .replace(/\{\{program_name\}\}/g, prog)
      .replace(/\{\{campaign_name\}\}/g, name)

  const closer = CTA_CLOSERS[input.ctaType] ?? CTA_CLOSERS.learn_more
  const body = `${fill(tpl.body)}\n\n${closer}`

  return {
    subject: fill(tpl.subject),
    body,
    alternateSubjects: tpl.alternates.map(fill),
    previewText: fill(tpl.body).split('\n').find(l => l.trim().length > 0)?.slice(0, 120) ?? '',
  }
}
