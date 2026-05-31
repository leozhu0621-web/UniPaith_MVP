// Spec 07 (Product Context §4) — student subscription API.
import apiClient from './client'
import type { Subscription, SubscribePayload } from '../types/billing'

export const getSubscription = (): Promise<Subscription> =>
  apiClient.get('/students/me/subscription').then(r => r.data)

export const subscribe = (payload: SubscribePayload): Promise<Subscription> =>
  apiClient.post('/students/me/subscription/subscribe', payload).then(r => r.data)

export const cancelSubscription = (): Promise<Subscription> =>
  apiClient.post('/students/me/subscription/cancel').then(r => r.data)

export const resumeSubscription = (): Promise<Subscription> =>
  apiClient.post('/students/me/subscription/resume').then(r => r.data)

export const setAdFree = (enabled: boolean): Promise<Subscription> =>
  apiClient.put('/students/me/subscription/ad-free', { enabled }).then(r => r.data)
