import apiClient from './client'
import { toArrayData } from './normalize'

export const getMyInterviews = () =>
  apiClient.get('/interviews/me').then(r => toArrayData<any>(r.data))

export const confirmInterview = (interviewId: string, confirmedTime: string) =>
  apiClient.post(`/interviews/${interviewId}/confirm`, { confirmed_time: confirmedTime }).then(r => r.data)

export const declineInterview = (interviewId: string) =>
  apiClient.post(`/interviews/${interviewId}/decline`).then(r => r.data)
