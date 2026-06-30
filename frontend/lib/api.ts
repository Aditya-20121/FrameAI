import type {
  UploadResponse,
  AnalysisResponse,
  RecommendationsResponse,
  GenerateResponse,
  GenerateStatusResponse,
  SessionResponse,
  CatalogueResponse,
} from './types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { credentials: 'include', ...init })
  const data = await res.json()
  if (!res.ok) throw data?.detail ?? data
  return data as T
}

export function uploadPhoto(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('photo', file)
  return apiFetch<UploadResponse>('/upload', { method: 'POST', body: form })
}

export function getAnalysis(jobId: string): Promise<AnalysisResponse> {
  return apiFetch<AnalysisResponse>(`/analysis/${jobId}`)
}

export function getRecommendations(jobId: string): Promise<RecommendationsResponse> {
  return apiFetch<RecommendationsResponse>(`/recommendations/${jobId}`)
}

export function postGenerate(jobId: string, frameId: string): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>('/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, frame_id: frameId }),
  })
}

export function getGenerateStatus(taskId: string): Promise<GenerateStatusResponse> {
  return apiFetch<GenerateStatusResponse>(`/generate/${taskId}`)
}

export function getSession(): Promise<SessionResponse> {
  return apiFetch<SessionResponse>('/session')
}

export function getCatalogue(params?: {
  style?: string
  retailer?: string
  limit?: number
  offset?: number
}): Promise<CatalogueResponse> {
  const qs = new URLSearchParams()
  if (params?.style)   qs.set('style',   params.style)
  if (params?.retailer) qs.set('retailer', params.retailer)
  qs.set('limit',  String(params?.limit  ?? 20))
  qs.set('offset', String(params?.offset ?? 0))
  return apiFetch<CatalogueResponse>(`/catalogue?${qs}`)
}

export function getCatalogueStyles(): Promise<{ styles: string[] }> {
  return apiFetch<{ styles: string[] }>('/catalogue/styles')
}
