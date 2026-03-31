import apiClient from './client'

export const getNotifications = (params?: { unread_only?: boolean; limit?: number; offset?: number }) =>
  apiClient.get('/notifications', { params }).then(r => r.data)

export const getUnreadCount = () =>
  apiClient.get('/notifications/unread-count').then(r => r.data)

export const markRead = (notificationId: string) =>
  apiClient.post(`/notifications/${notificationId}/read`).then(r => r.data)

export const markAllRead = () =>
  apiClient.post('/notifications/read-all').then(r => r.data)

export const getNotificationPrefs = () =>
  apiClient.get('/notifications/preferences').then(r => r.data)

export const updateNotificationPrefs = (data: { email_enabled: boolean; preferences: Record<string, boolean> }) =>
  apiClient.put('/notifications/preferences', data).then(r => r.data)
