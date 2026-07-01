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
const SESSION_KEY = '_frameai_token'

// In-memory fallback for environments where localStorage is unavailable
// (iOS Private Browsing, storage-restricted contexts, etc.)
let _memToken: string | null = null

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return localStorage.getItem(SESSION_KEY) ?? _memToken
  } catch {
    return _memToken
  }
}

function storeToken(token: string): void {
  _memToken = token
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(SESSION_KEY, token)
  } catch {
    // localStorage unavailable (Private Browsing quota exceeded, etc.)
    // _memToken already set above — session survives the current page lifetime
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken()
  const res = await fetch(`${API}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      ...(init?.headers as Record<string, string> | undefined),
      ...(token ? { 'X-Session-Token': token } : {}),
    },
  })
  const data = await res.json()
  if (!res.ok) throw data?.detail ?? data
  return data as T
}

export async function uploadPhoto(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('photo', file)
  const result = await apiFetch<UploadResponse>('/upload', { method: 'POST', body: form })
  if (result.session_token) storeToken(result.session_token)
  return result
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
  if (params?.style)    qs.set('style',    params.style)
  if (params?.retailer) qs.set('retailer', params.retailer)
  qs.set('limit',  String(params?.limit  ?? 20))
  qs.set('offset', String(params?.offset ?? 0))
  return apiFetch<CatalogueResponse>(`/catalogue?${qs}`)
}

export function getCatalogueStyles(): Promise<{ styles: string[] }> {
  return apiFetch<{ styles: string[] }>('/catalogue/styles')
}
