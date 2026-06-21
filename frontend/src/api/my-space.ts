import apiClient from './client'

export type MySpaceOwner = 'student' | 'recommender' | 'institution' | 'system'
export type MySpaceUrgency = 'focus_now' | 'priority_window' | 'gentle_attention' | 'neutral'
export type MySpaceReadinessStatus = 'ready' | 'needs_attention' | 'blocked' | 'unknown'

export interface MySpaceProvenance {
  source: string
  label: string
  href: string | null
  confidence: number | null
  updated_at: string | null
}

export interface MySpaceTask {
  key: string
  title: string
  description: string
  owner: MySpaceOwner
  urgency: MySpaceUrgency
  category: string
  cta_label: string
  cta_route: string
  blocker: string | null
  missing_field: string | null
  due_at: string | null
  provenance: MySpaceProvenance[]
  dismissed: boolean
  snoozed_until: string | null
  active: boolean
  dismissible: boolean
}

export interface MySpaceReadiness {
  key: string
  label: string
  status: MySpaceReadinessStatus
  pct: number | null
  detail: string
  route: string
  provenance: MySpaceProvenance[]
}

export interface MySpaceMetric {
  key: string
  label: string
  value: number | string
  route: string
  status: MySpaceReadinessStatus | null
}

export interface MySpaceModuleItem {
  key: string
  title: string
  description: string
  route: string
  owner: MySpaceOwner | null
  urgency: MySpaceUrgency
  status: string | null
  due_at: string | null
  provenance: MySpaceProvenance[]
}

export interface MySpaceOverview {
  generated_at: string
  student: {
    id: string
    first_name: string | null
    display_name: string | null
  }
  readiness: MySpaceReadiness[]
  tasks: MySpaceTask[]
  pipeline: MySpaceMetric[]
  evidence_gaps: MySpaceTask[]
  deadlines: MySpaceModuleItem[]
  waiting_on: MySpaceModuleItem[]
  messages: MySpaceModuleItem[]
  feedback: MySpaceModuleItem[]
  strategy: MySpaceModuleItem | null
  prep_readiness: MySpaceReadiness[]
  offers: MySpaceModuleItem[]
  saved_targets: MySpaceModuleItem[]
  import_status: MySpaceModuleItem
  recent_changes: MySpaceModuleItem[]
  access_issues: MySpaceProvenance[]
}

export interface MySpaceTaskPatch {
  dismissed?: boolean
  snoozed_until?: string | null
}

export interface MySpaceTaskStateResponse {
  task_key: string
  dismissed: boolean
  snoozed_until: string | null
}

export const getMySpaceOverview = () =>
  apiClient.get<MySpaceOverview>('/students/me/my-space/overview').then(r => r.data)

export const patchMySpaceTask = (taskKey: string, data: MySpaceTaskPatch) =>
  apiClient
    .patch<MySpaceTaskStateResponse>(
      `/students/me/my-space/tasks/${encodeURIComponent(taskKey)}`,
      data,
    )
    .then(r => r.data)
