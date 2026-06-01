import apiClient from './client'
import { toArrayData } from './normalize'
import type { Interview } from '../types'

export const getMyInterviews = (): Promise<Interview[]> =>
  apiClient.get('/interviews/me').then(r => toArrayData<Interview>(r.data))

export const confirmInterview = (interviewId: string, confirmedTime: string | null) =>
  apiClient
    .post(`/interviews/${interviewId}/confirm`, { confirmed_time: confirmedTime })
    .then(r => r.data as Interview)

export const declineInterview = (interviewId: string) =>
  apiClient.post(`/interviews/${interviewId}/decline`).then(r => r.data as Interview)

export const requestInterviewReschedule = (interviewId: string) =>
  apiClient.post(`/interviews/${interviewId}/request-reschedule`).then(r => r.data as Interview)
