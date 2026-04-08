import apiClient from './client'

export const getProfile = () => apiClient.get('/students/me/profile').then(r => r.data)
export const updateProfile = (data: any) => apiClient.put('/students/me/profile', data).then(r => r.data)

export const getOnboarding = () => apiClient.get('/students/me/onboarding').then(r => r.data)
export const getNextStep = () => apiClient.get('/students/me/onboarding/next-step').then(r => r.data)

export const listAcademics = () => apiClient.get('/students/me/academics').then(r => r.data)
export const createAcademic = (data: any) => apiClient.post('/students/me/academics', data).then(r => r.data)
export const updateAcademic = (id: string, data: any) => apiClient.put(`/students/me/academics/${id}`, data).then(r => r.data)
export const deleteAcademic = (id: string) => apiClient.delete(`/students/me/academics/${id}`)

export const listCourses = (recordId: string) => apiClient.get(`/students/me/academics/${recordId}/courses`).then(r => r.data)
export const createCourse = (recordId: string, data: any) => apiClient.post(`/students/me/academics/${recordId}/courses`, data).then(r => r.data)
export const updateCourse = (recordId: string, courseId: string, data: any) => apiClient.put(`/students/me/academics/${recordId}/courses/${courseId}`, data).then(r => r.data)
export const deleteCourse = (recordId: string, courseId: string) => apiClient.delete(`/students/me/academics/${recordId}/courses/${courseId}`)

export const listTestScores = () => apiClient.get('/students/me/test-scores').then(r => r.data)
export const createTestScore = (data: any) => apiClient.post('/students/me/test-scores', data).then(r => r.data)
export const updateTestScore = (id: string, data: any) => apiClient.put(`/students/me/test-scores/${id}`, data).then(r => r.data)
export const deleteTestScore = (id: string) => apiClient.delete(`/students/me/test-scores/${id}`)

export const listActivities = () => apiClient.get('/students/me/activities').then(r => r.data)
export const createActivity = (data: any) => apiClient.post('/students/me/activities', data).then(r => r.data)
export const updateActivity = (id: string, data: any) => apiClient.put(`/students/me/activities/${id}`, data).then(r => r.data)
export const deleteActivity = (id: string) => apiClient.delete(`/students/me/activities/${id}`)

export const getAccommodations = () => apiClient.get('/students/me/accommodations').then(r => r.data)
export const upsertAccommodations = (data: any) => apiClient.put('/students/me/accommodations', data).then(r => r.data)

export const listCompetitions = () => apiClient.get('/students/me/competitions').then(r => r.data)
export const createCompetition = (data: any) => apiClient.post('/students/me/competitions', data).then(r => r.data)
export const updateCompetition = (id: string, data: any) => apiClient.put(`/students/me/competitions/${id}`, data).then(r => r.data)
export const deleteCompetition = (id: string) => apiClient.delete(`/students/me/competitions/${id}`)

export const listWorkExperiences = () => apiClient.get('/students/me/work-experiences').then(r => r.data)
export const createWorkExperience = (data: any) => apiClient.post('/students/me/work-experiences', data).then(r => r.data)
export const updateWorkExperience = (id: string, data: any) => apiClient.put(`/students/me/work-experiences/${id}`, data).then(r => r.data)
export const deleteWorkExperience = (id: string) => apiClient.delete(`/students/me/work-experiences/${id}`)

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

export const getVisaInfo = () => apiClient.get('/students/me/visa-info').then(r => r.data)
export const upsertVisaInfo = (data: any) => apiClient.put('/students/me/visa-info', data).then(r => r.data)

export const getScheduling = () => apiClient.get('/students/me/scheduling').then(r => r.data)
export const upsertScheduling = (data: any) => apiClient.put('/students/me/scheduling', data).then(r => r.data)

export const getPeerComparison = () => apiClient.get('/students/me/peer-comparison').then(r => r.data)

export const getAnalytics = () => apiClient.get('/students/me/analytics').then(r => r.data)

export const getTimeline = () => apiClient.get('/students/me/timeline').then(r => r.data)

export const getPreferences = () => apiClient.get('/students/me/preferences').then(r => r.data)
export const upsertPreferences = (data: any) => apiClient.put('/students/me/preferences', data).then(r => r.data)
