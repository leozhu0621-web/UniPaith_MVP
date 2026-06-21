const MANAGE_TAB_TARGETS: Record<string, string> = {
  applications: '/s/applications',
  calendar: '/s/calendar',
  messages: '/s/messages',
  prompts: '/s/prep?tab=prompts',
  workshops: '/s/prep?tab=workshops',
}

export function resolveManageRedirect(params: URLSearchParams): string {
  const tab = params.get('tab')
  const rest = new URLSearchParams(params)
  rest.delete('tab')

  const base = tab ? MANAGE_TAB_TARGETS[tab] ?? '/s/space' : '/s/space'
  const qs = rest.toString()
  if (!qs) return base

  return `${base}${base.includes('?') ? '&' : '?'}${qs}`
}
