import apiClient from './client'

export const getMyInterviews = () =>
  apiClient.get('/interviews/me').then(r => r.data)

export const confirmInterview = (interviewId: string, confirmedTime: string) =>
  apiClient.post(`/interviews/${interviewId}/confirm`, { confirmed_time: confirmedTime }).then(r => r.data)
