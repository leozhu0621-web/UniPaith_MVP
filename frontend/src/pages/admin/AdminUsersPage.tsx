import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers, activateUser, deactivateUser } from '../../api/admin'
import { formatRelative } from '../../utils/format'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { useToastStore } from '../../stores/toast-store'
import { errorMessage } from '../../utils/errors'
import { Users, UserCheck, UserX, Filter } from 'lucide-react'

interface AdminUserRow {
  id: string
  email: string
  role: string
  is_active?: boolean
  created_at: string
}

export default function AdminUsersPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [page, setPage] = useState(0)
  const limit = 25

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'users', roleFilter, page],
    queryFn: () => getUsers({ role: roleFilter || undefined, skip: page * limit, limit }),
  })

  const deactivateMut = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      addToast('User deactivated', 'success')
    },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })

  const activateMut = useMutation({
    mutationFn: activateUser,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      addToast('User activated', 'success')
    },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })

  const users: AdminUserRow[] = (Array.isArray(data) ? data : data?.users ?? data?.items ?? []) as AdminUserRow[]

  if (isLoading) {
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
          <span className="text-sm text-gray-500">{users.length} users shown</span>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <Filter size={16} className="text-gray-400" />
          <span className="text-sm font-medium text-gray-600">Filter by role:</span>
          {['', 'student', 'institution_admin', 'admin'].map(role => (
            <button
              key={role}
              onClick={() => { setRoleFilter(role); setPage(0) }}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                roleFilter === role
                  ? 'bg-indigo-100 text-indigo-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {role === '' ? 'All' : role === 'institution_admin' ? 'Institution' : role.charAt(0).toUpperCase() + role.slice(1)}
            </button>
          ))}
        </div>
      </Card>

      {/* User Table */}
      <Card className="overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-400">
                  No users found
                </td>
              </tr>
            ) : (
              users.map(u => (
                <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-gray-900">{u.email}</p>
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
                          onClick={() => deactivateMut.mutate(u.id)}
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
                          onClick={() => activateMut.mutate(u.id)}
                          disabled={activateMut.isPending}
                        >
                          <UserCheck size={14} className="mr-1" />
                          Activate
                        </Button>
                      )
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
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setPage(p => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          Previous
        </Button>
        <span className="text-sm text-gray-500">Page {page + 1}</span>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setPage(p => p + 1)}
          disabled={users.length < limit}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
