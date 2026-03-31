import apiClient from './client'

export const loginApi = (email: string, password: string) =>
  apiClient.post('/auth/login', { email, password }).then(r => r.data)

export const signupApi = (email: string, password: string, role: string) =>
  apiClient.post('/auth/signup', { email, password, role }).then(r => r.data)

export const refreshTokenApi = (refreshToken: string) =>
  apiClient.post('/auth/refresh', { refresh_token: refreshToken }).then(r => r.data)

export const getMeApi = () =>
  apiClient.get('/auth/me').then(r => r.data)
