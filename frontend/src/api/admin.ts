import apiClient from './client'

export const getSystemStats = () =>
  apiClient.get('/admin/dashboard/stats').then(r => r.data)
