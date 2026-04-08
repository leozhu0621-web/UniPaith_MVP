import apiClient from './client'

export const getProfile = () => apiClient.get('/students/me/profile').then(r => r.data)
export const updateProfile = (data: any) => apiClient.put('/students/me/profile', data).then(r => r.data)

export const getOnboarding = () => apiClient.get('/students/me/onboarding').then(r => r.data)
export const getNextStep = () => apiClient.get('/students/me/onboarding/next-step').then(r => r.data)

export const listAcademics = () => apiClient.get('/students/me/academics').then(r => r.data)
export const createAcademic = (data: any) => apiClient.post('/students/me/academics', data).then(r => r.data)
export const updateAcademic = (id: string, data: any) => apiClient.put(`/students/me/academics/${id}`, data).then(r => r.data)
export const deleteAcademic = (id: string) => apiClient.delete(`/students/me/academics/${id}`)

export const listTestScores = () => apiClient.get('/students/me/test-scores').then(r => r.data)
export const createTestScore = (data: any) => apiClient.post('/students/me/test-scores', data).then(r => r.data)
export const updateTestScore = (id: string, data: any) => apiClient.put(`/students/me/test-scores/${id}`, data).then(r => r.data)
export const deleteTestScore = (id: string) => apiClient.delete(`/students/me/test-scores/${id}`)

export const listActivities = () => apiClient.get('/students/me/activities').then(r => r.data)
export const createActivity = (data: any) => apiClient.post('/students/me/activities', data).then(r => r.data)
export const updateActivity = (id: string, data: any) => apiClient.put(`/students/me/activities/${id}`, data).then(r => r.data)
export const deleteActivity = (id: string) => apiClient.delete(`/students/me/activities/${id}`)

export const listLanguages = () => apiClient.get('/students/me/languages').then(r => r.data)
export const createLanguage = (data: any) => apiClient.post('/students/me/languages', data).then(r => r.data)
export const updateLanguage = (id: string, data: any) => apiClient.put(`/students/me/languages/${id}`, data).then(r => r.data)
export const deleteLanguage = (id: string) => apiClient.delete(`/students/me/languages/${id}`)

export const listResearch = () => apiClient.get('/students/me/research').then(r => r.data)
export const createResearch = (data: any) => apiClient.post('/students/me/research', data).then(r => r.data)
export const updateResearch = (id: string, data: any) => apiClient.put(`/students/me/research/${id}`, data).then(r => r.data)
export const deleteResearch = (id: string) => apiClient.delete(`/students/me/research/${id}`)

export const listPortfolio = () => apiClient.get('/students/me/portfolio').then(r => r.data)
export const createPortfolioItem = (data: any) => apiClient.post('/students/me/portfolio', data).then(r => r.data)
export const updatePortfolioItem = (id: string, data: any) => apiClient.put(`/students/me/portfolio/${id}`, data).then(r => r.data)
export const deletePortfolioItem = (id: string) => apiClient.delete(`/students/me/portfolio/${id}`)

export const listOnlinePresence = () => apiClient.get('/students/me/online-presence').then(r => r.data)
export const createOnlinePresence = (data: any) => apiClient.post('/students/me/online-presence', data).then(r => r.data)
export const updateOnlinePresence = (id: string, data: any) => apiClient.put(`/students/me/online-presence/${id}`, data).then(r => r.data)
export const deleteOnlinePresence = (id: string) => apiClient.delete(`/students/me/online-presence/${id}`)

export const getPreferences = () => apiClient.get('/students/me/preferences').then(r => r.data)
export const upsertPreferences = (data: any) => apiClient.put('/students/me/preferences', data).then(r => r.data)
