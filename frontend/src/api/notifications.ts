import apiClient from './client'
import type { EmailFrequency, NotificationChannels, NotificationPreference } from '../types'

export const getNotifications = (params?: { unread_only?: boolean; limit?: number; offset?: number }) =>
  apiClient.get('/notifications', { params }).then(r => r.data)

export const getUnreadCount = () =>
  apiClient.get('/notifications/unread-count').then(r => r.data)

export const markRead = (notificationId: string) =>
  apiClient.post(`/notifications/${notificationId}/read`).then(r => r.data)

export const markAllRead = () =>
  apiClient.post('/notifications/read-all').then(r => r.data)

export const getNotificationPrefs = (): Promise<NotificationPreference> =>
  apiClient.get('/notifications/preferences').then(r => r.data)

export const updateNotificationPrefs = (data: {
  email_enabled?: boolean
  email_frequency?: EmailFrequency
  preferences?: Record<string, NotificationChannels>
}): Promise<NotificationPreference> =>
  apiClient.put('/notifications/preferences', data).then(r => r.data)
