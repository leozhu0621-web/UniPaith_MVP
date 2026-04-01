import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  activateUser,
  bulkSetUsersActive,
  bulkVerifyInstitutions,
  deactivateUser,
  getAdminActionAudit,
  getUsers,
  verifyInstitution,
} from '../../api/admin'
import { formatRelative } from '../../utils/format'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import Input from '../../components/ui/Input'
import Modal from '../../components/ui/Modal'
import { useToastStore } from '../../stores/toast-store'
import {
  AlertTriangle,
  CheckCircle,
  Filter,
  Search,
  UserCheck,
  UserX,
  Users,
} from 'lucide-react'

type AdminUserRow = {
  id: string
  email: string
  role: 'student' | 'institution_admin' | 'admin'
  is_active: boolean
  created_at: string | null
  institution_id?: string | null
  institution_verified?: boolean | null
}

type PendingAction =
  | { type: 'activate'; userIds: string[]; reason: string }
  | { type: 'deactivate'; userIds: string[]; reason: string }
  | { type: 'verify'; institutionIds: string[]; reason: string }
  | null

export default function AdminUsersPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [queryInput, setQueryInput] = useState('')
  const [query, setQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState(1)
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [selectedInstitutionIds, setSelectedInstitutionIds] = useState<string[]>([])
  const [pendingAction, setPendingAction] = useState<PendingAction>(null)
  const pageSize = 25

  const usersQ = useQuery({
    queryKey: ['admin', 'users', query, roleFilter, statusFilter, page, pageSize],
    queryFn: () =>
      getUsers({
        q: query || undefined,
        role: roleFilter || undefined,
        is_active:
          statusFilter === 'all' ? undefined : statusFilter === 'active',
        page,
        page_size: pageSize,
      }),
  })

  const deactivateMut = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason?: string }) =>
      deactivateUser(userId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      addToast('User deactivated', 'success')
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const activateMut = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason?: string }) =>
      activateUser(userId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      addToast('User activated', 'success')
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const verifyMut = useMutation({
    mutationFn: ({ institutionId, reason }: { institutionId: string; reason?: string }) =>
      verifyInstitution(institutionId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      addToast('Institution verified', 'success')
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const bulkUsersMut = useMutation({
    mutationFn: ({
      userIds,
      active,
      reason,
    }: {
      userIds: string[]
      active: boolean
      reason?: string
    }) => bulkSetUsersActive({ user_ids: userIds, active, reason }),
    onSuccess: (data: any) => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      setSelectedUserIds([])
      addToast(
        `Updated ${data?.updated_count ?? 0} users (${data?.not_found_user_ids?.length ?? 0} not found)`,
        'success',
      )
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const bulkVerifyMut = useMutation({
    mutationFn: ({ institutionIds, reason }: { institutionIds: string[]; reason?: string }) =>
      bulkVerifyInstitutions({ institution_ids: institutionIds, reason }),
    onSuccess: (data: any) => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      setSelectedInstitutionIds([])
      addToast(
        `Verified ${data?.verified_count ?? 0} institutions (${data?.not_found_institution_ids?.length ?? 0} not found)`,
        'success',
      )
    },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const auditQ = useQuery({
    queryKey: ['admin', 'audit', 'actions', 'users'],
    queryFn: () => getAdminActionAudit({ limit: 8 }),
    refetchInterval: 10000,
  })

  const users: AdminUserRow[] = usersQ.data?.items ?? []
  const total = usersQ.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const selectableUserIds = users.filter(u => u.role !== 'admin').map(u => u.id)
  const selectableInstitutionIds = users
    .filter(
      u =>
        u.role === 'institution_admin' &&
        Boolean(u.institution_id) &&
        u.institution_verified !== true,
    )
    .map(u => u.institution_id as string)

  const allUsersOnPageSelected =
    selectableUserIds.length > 0 &&
    selectableUserIds.every(id => selectedUserIds.includes(id))
  const allInstitutionsOnPageSelected =
    selectableInstitutionIds.length > 0 &&
    selectableInstitutionIds.every(id => selectedInstitutionIds.includes(id))

  const activeUsers = users.filter(u => u.is_active !== false).length
  const studentUsers = users.filter(u => u.role === 'student').length
  const institutionUsers = users.filter(u => u.role === 'institution_admin').length
  const inactiveRecentCohort = useMemo(
    () =>
      users.filter(u => {
        if (u.is_active !== false || !u.created_at) return false
        const createdAt = new Date(u.created_at).getTime()
        return Date.now() - createdAt <= 30 * 24 * 60 * 60 * 1000
      }).length,
    [users],
  )
  const unverifiedInstitutions = users.filter(
    u =>
      u.role === 'institution_admin' &&
      Boolean(u.institution_id) &&
      u.institution_verified !== true,
  ).length

  if (usersQ.isLoading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500">View, activate, and deactivate user accounts</p>
        </div>
        <div className="flex items-center gap-2">
          <Users size={16} className="text-gray-400" />
          <span className="text-sm text-gray-500">{total} users total</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Visible Users</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{users.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Active</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{activeUsers}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Students</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">{studentUsers}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Institution Admins</p>
          <p className="text-2xl font-bold text-purple-600 mt-1">{institutionUsers}</p>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-500" />
            <p className="text-sm font-medium text-gray-700">Needs attention</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border border-gray-200 p-3">
            <p className="text-xs text-gray-500">Inactive users in last 30 days</p>
            <p className="text-xl font-semibold text-amber-700 mt-1">{inactiveRecentCohort}</p>
            <Button
              size="sm"
              variant="secondary"
              className="mt-2"
              onClick={() => {
                setStatusFilter('inactive')
                setPage(1)
              }}
            >
              Review inactive users
            </Button>
          </div>
          <div className="rounded-lg border border-gray-200 p-3">
            <p className="text-xs text-gray-500">Unverified institutions (on this page)</p>
            <p className="text-xl font-semibold text-amber-700 mt-1">{unverifiedInstitutions}</p>
            <Button
              size="sm"
              variant="secondary"
              className="mt-2"
              onClick={() => {
                setRoleFilter('institution_admin')
                setPage(1)
              }}
            >
              Review institutions
            </Button>
          </div>
        </div>
      </Card>

      {/* Triage Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
          <div className="lg:col-span-2">
            <div className="relative">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />
              <Input
                value={queryInput}
                onChange={e => setQueryInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    setQuery(queryInput.trim())
                    setPage(1)
                  }
                }}
                placeholder="Search by email"
                className="pl-9"
              />
            </div>
          </div>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            value={roleFilter}
            onChange={e => {
              setRoleFilter(e.target.value)
              setPage(1)
            }}
          >
            <option value="">All roles</option>
            <option value="student">Student</option>
            <option value="institution_admin">Institution</option>
            <option value="admin">Admin</option>
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            value={statusFilter}
            onChange={e => {
              setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')
              setPage(1)
            }}
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Filter size={16} className="text-gray-400" />
          <Button
            size="sm"
            onClick={() => {
              setQuery(queryInput.trim())
              setPage(1)
            }}
          >
            Apply filters
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              setQueryInput('')
              setQuery('')
              setRoleFilter('')
              setStatusFilter('all')
              setPage(1)
            }}
          >
            Reset
          </Button>
        </div>
      </Card>

      {(selectedUserIds.length > 0 || selectedInstitutionIds.length > 0) && (
        <Card className="p-3 border-indigo-200 bg-indigo-50">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-indigo-900">
              Selected: {selectedUserIds.length} users, {selectedInstitutionIds.length}{' '}
              institutions
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                disabled={selectedUserIds.length === 0}
                onClick={() =>
                  setPendingAction({ type: 'activate', userIds: selectedUserIds, reason: '' })
                }
              >
                <UserCheck size={14} className="mr-1" />
                Bulk activate users
              </Button>
              <Button
                size="sm"
                variant="secondary"
                className="text-red-700 border-red-200 hover:bg-red-50"
                disabled={selectedUserIds.length === 0}
                onClick={() =>
                  setPendingAction({ type: 'deactivate', userIds: selectedUserIds, reason: '' })
                }
              >
                <UserX size={14} className="mr-1" />
                Bulk deactivate users
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={selectedInstitutionIds.length === 0}
                onClick={() =>
                  setPendingAction({
                    type: 'verify',
                    institutionIds: selectedInstitutionIds,
                    reason: '',
                  })
                }
              >
                <CheckCircle size={14} className="mr-1" />
                Bulk verify institutions
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* User Table */}
      <Card className="overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Institution</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-sm text-gray-400">
                  No users found
                </td>
              </tr>
            ) : (
              users.map(u => (
                <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(u.id)}
                        disabled={u.role === 'admin'}
                        onChange={e =>
                          setSelectedUserIds(prev =>
                            e.target.checked
                              ? Array.from(new Set([...prev, u.id]))
                              : prev.filter(id => id !== u.id),
                          )
                        }
                      />
                      <p className="text-sm font-medium text-gray-900">{u.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={
                      u.role === 'student' ? 'info' :
                      u.role === 'institution_admin' ? 'success' :
                      u.role === 'admin' ? 'warning' : 'neutral'
                    }>
                      {u.role}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={u.is_active !== false ? 'success' : 'danger'}>
                      {u.is_active !== false ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    {u.institution_id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedInstitutionIds.includes(u.institution_id)}
                          disabled={u.institution_verified === true}
                          onChange={e =>
                            setSelectedInstitutionIds(prev =>
                              e.target.checked
                                ? Array.from(new Set([...prev, u.institution_id as string]))
                                : prev.filter(id => id !== u.institution_id),
                            )
                          }
                        />
                        <Badge
                          variant={u.institution_verified ? 'success' : 'warning'}
                        >
                          {u.institution_verified ? 'Verified' : 'Unverified'}
                        </Badge>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatRelative(u.created_at)}
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-xs text-gray-400 font-mono">{u.id?.slice(0, 8)}...</code>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {u.role !== 'admin' && (
                      u.is_active !== false ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            setPendingAction({ type: 'deactivate', userIds: [u.id], reason: '' })
                          }
                          disabled={deactivateMut.isPending}
                          className="text-red-600 border-red-200 hover:bg-red-50"
                        >
                          <UserX size={14} className="mr-1" />
                          Deactivate
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            setPendingAction({ type: 'activate', userIds: [u.id], reason: '' })
                          }
                          disabled={activateMut.isPending}
                        >
                          <UserCheck size={14} className="mr-1" />
                          Activate
                        </Button>
                      )
                    )}
                    {u.institution_id && u.institution_verified !== true && (
                      <Button
                        size="sm"
                        variant="secondary"
                        className="ml-2"
                        onClick={() =>
                          setPendingAction({
                            type: 'verify',
                            institutionIds: [u.institution_id as string],
                            reason: '',
                          })
                        }
                        disabled={verifyMut.isPending}
                      >
                        <CheckCircle size={14} className="mr-1" />
                        Verify institution
                      </Button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={allUsersOnPageSelected}
            onChange={e =>
              setSelectedUserIds(prev =>
                e.target.checked
                  ? Array.from(new Set([...prev, ...selectableUserIds]))
                  : prev.filter(id => !selectableUserIds.includes(id)),
              )
            }
          />
          <span className="text-xs text-gray-500">Select all users on this page</span>
          <input
            type="checkbox"
            checked={allInstitutionsOnPageSelected}
            onChange={e =>
              setSelectedInstitutionIds(prev =>
                e.target.checked
                  ? Array.from(new Set([...prev, ...selectableInstitutionIds]))
                  : prev.filter(id => !selectableInstitutionIds.includes(id)),
              )
            }
            className="ml-4"
          />
          <span className="text-xs text-gray-500">Select all institutions on this page</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-500">
            Page {page} / {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      </div>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-gray-700">Recent admin actions</p>
          <span className="text-xs text-gray-500">Quick feed</span>
        </div>
        <div className="space-y-2">
          {(auditQ.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No recent actions yet.</p>
          ) : (
            (auditQ.data?.items ?? []).map((event: any) => (
              <div key={event.id} className="rounded-lg border border-gray-200 p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{event.action}</p>
                  <span className="text-xs text-gray-500">{formatRelative(event.created_at)}</span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {event.entity_type} · {event.entity_id}
                </p>
              </div>
            ))
          )}
        </div>
      </Card>

      <Modal
        isOpen={pendingAction !== null}
        onClose={() => setPendingAction(null)}
        title="Confirm admin action"
        size="md"
      >
        {pendingAction && (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              {pendingAction.type === 'activate' &&
                `Activate ${pendingAction.userIds.length} user(s)?`}
              {pendingAction.type === 'deactivate' &&
                `Deactivate ${pendingAction.userIds.length} user(s)?`}
              {pendingAction.type === 'verify' &&
                `Verify ${pendingAction.institutionIds.length} institution(s)?`}
            </p>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Reason (optional)
              </label>
              <Input
                value={pendingAction.reason}
                onChange={e =>
                  setPendingAction(prev =>
                    prev ? { ...prev, reason: e.target.value } : prev,
                  )
                }
                placeholder="e.g. Compliance cleanup for inactive accounts"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => setPendingAction(null)}
                disabled={
                  activateMut.isPending ||
                  deactivateMut.isPending ||
                  verifyMut.isPending ||
                  bulkUsersMut.isPending ||
                  bulkVerifyMut.isPending
                }
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (!pendingAction) return
                  if (pendingAction.type === 'activate') {
                    if (pendingAction.userIds.length === 1) {
                      activateMut.mutate({
                        userId: pendingAction.userIds[0],
                        reason: pendingAction.reason || undefined,
                      })
                    } else {
                      bulkUsersMut.mutate({
                        userIds: pendingAction.userIds,
                        active: true,
                        reason: pendingAction.reason || undefined,
                      })
                    }
                  } else if (pendingAction.type === 'deactivate') {
                    if (pendingAction.userIds.length === 1) {
                      deactivateMut.mutate({
                        userId: pendingAction.userIds[0],
                        reason: pendingAction.reason || undefined,
                      })
                    } else {
                      bulkUsersMut.mutate({
                        userIds: pendingAction.userIds,
                        active: false,
                        reason: pendingAction.reason || undefined,
                      })
                    }
                  } else {
                    if (pendingAction.institutionIds.length === 1) {
                      verifyMut.mutate({
                        institutionId: pendingAction.institutionIds[0],
                        reason: pendingAction.reason || undefined,
                      })
                    } else {
                      bulkVerifyMut.mutate({
                        institutionIds: pendingAction.institutionIds,
                        reason: pendingAction.reason || undefined,
                      })
                    }
                  }
                  setPendingAction(null)
                }}
                disabled={
                  activateMut.isPending ||
                  deactivateMut.isPending ||
                  verifyMut.isPending ||
                  bulkUsersMut.isPending ||
                  bulkVerifyMut.isPending
                }
              >
                Confirm
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
