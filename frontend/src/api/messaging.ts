import apiClient from './client'

export const getConversations = () =>
  apiClient.get('/messages/conversations').then(r => r.data)

export const createConversation = (data: { institution_id: string; subject?: string; program_id?: string; student_id?: string }) =>
  apiClient.post('/messages/conversations', data).then(r => r.data)

export const getMessages = (convId: string, params?: { limit?: number; before?: string }) =>
  apiClient.get(`/messages/conversations/${convId}`, { params }).then(r => r.data)

export const sendMessage = (convId: string, content: string) =>
  apiClient.post(`/messages/conversations/${convId}`, { content }).then(r => r.data)
