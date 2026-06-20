export const MY_SPACE_ROUTES = ['/s/space', '/s/import', '/s/profile', '/s/saved', '/s/prep', '/s/applications', '/s/calendar']

export function isMySpacePath(pathname: string) {
  return MY_SPACE_ROUTES.some(path => pathname === path || pathname.startsWith(`${path}/`))
}
