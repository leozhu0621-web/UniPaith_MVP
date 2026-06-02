// Specs 48–53 — public build-transparency client. No auth required; the
// endpoints expose only build architecture (phases, feature coverage, the live
// route map, the live table map, the acceptance gates, the UX interaction bar),
// never user data.
import apiClient from './client'
import type {
  Acceptance,
  ApiContract,
  BuildOverview,
  ChatbotEval,
  DataModel,
  FeatureCatalog,
  FrontendStandards,
  Production,
  Roadmap,
  SearchBuild,
  UxBenchmark,
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

export async function getUxBenchmark(): Promise<UxBenchmark> {
  const { data } = await apiClient.get<UxBenchmark>('/build/ux-benchmark')
  return data
}

export async function getFrontendStandards(): Promise<FrontendStandards> {
  const { data } = await apiClient.get<FrontendStandards>('/build/frontend-standards')
  return data
}

export async function getProduction(): Promise<Production> {
  const { data } = await apiClient.get<Production>('/build/production')
  return data
}

export async function getSearchBuild(): Promise<SearchBuild> {
  const { data } = await apiClient.get<SearchBuild>('/build/search')
  return data
}

export async function getChatbotEval(): Promise<ChatbotEval> {
  const { data } = await apiClient.get<ChatbotEval>('/build/chatbot-eval')
  return data
}
