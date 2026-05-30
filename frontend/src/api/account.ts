import apiClient from './client'

export interface Account {
  id: string
  email: string
  role: string
  locale: string | null
  timezone: string | null
  deletion_requested_at: string | null
  created_at: string
}

export const getAccount = (): Promise<Account> =>
  apiClient.get('/me/account').then(r => r.data)

export const updateAccount = (body: { locale?: string | null; timezone?: string | null }) =>
  apiClient.patch('/me/account', body).then(r => r.data as Account)

export const requestAccountDeletion = () =>
  apiClient.post('/me/account/request-deletion').then(r => r.data as {
    deletion_requested_at: string
    grace_period_days: number
    purge_after: string
  })

export const cancelAccountDeletion = () =>
  apiClient.post('/me/account/cancel-deletion').then(r => r.data)

export const changePassword = (current_password: string, new_password: string) =>
  apiClient.post('/me/account/change-password', { current_password, new_password })
