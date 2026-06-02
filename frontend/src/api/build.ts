// Specs 48–52 — public build-transparency client. No auth required; the
// endpoints expose only build architecture (phases, feature coverage, the live
// route map, the live table map, the acceptance gates), never user data.
import apiClient from './client'
import type {
  Acceptance,
  ApiContract,
  BuildOverview,
  DataModel,
  FeatureCatalog,
  Roadmap,
} from '../types/build'

export async function getBuildOverview(): Promise<BuildOverview> {
  const { data } = await apiClient.get<BuildOverview>('/build/overview')
  return data
}

export async function getRoadmap(): Promise<Roadmap> {
  const { data } = await apiClient.get<Roadmap>('/build/roadmap')
  return data
}

export async function getFeatureCatalog(): Promise<FeatureCatalog> {
  const { data } = await apiClient.get<FeatureCatalog>('/build/features')
  return data
}

export async function getApiContract(): Promise<ApiContract> {
  const { data } = await apiClient.get<ApiContract>('/build/api-contract')
  return data
}

export async function getDataModel(): Promise<DataModel> {
  const { data } = await apiClient.get<DataModel>('/build/data-model')
  return data
}

export async function getAcceptance(): Promise<Acceptance> {
  const { data } = await apiClient.get<Acceptance>('/build/acceptance')
  return data
}
