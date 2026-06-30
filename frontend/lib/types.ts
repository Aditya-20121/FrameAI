export type FaceShape  = 'oval' | 'round' | 'square' | 'heart' | 'diamond' | 'oblong'
export type Undertone  = 'warm' | 'cool' | 'neutral'
export type SizeBand   = 'narrow' | 'standard' | 'wide'
export type Jawline    = 'angular' | 'soft' | 'tapered'
export type Cheekbones = 'high' | 'normal' | 'low'
export type EyeSet     = 'close' | 'average' | 'wide'
export type SkinDepth  = 'fair' | 'light' | 'medium' | 'olive' | 'deep'

export interface UploadResponse {
  job_id: string
  status: string
  session_token: string  // Stored in localStorage, sent as X-Session-Token header on all subsequent requests
}

export interface AnalysisResponse {
  job_id: string
  status: 'processing' | 'complete' | 'failed'
  face_shape?: FaceShape
  face_shape_confidence?: number
  face_shape_explanation?: string
  jawline?: Jawline
  cheekbones?: Cheekbones
  eye_set?: EyeSet
  undertone?: Undertone
  undertone_confidence?: number
  undertone_hex?: string
  skin_depth?: SkinDepth
  ipd_mm?: number
  size_band?: SizeBand
}

export interface Frame {
  frame_id: string
  rank: number
  name: string
  style: string
  colour: string
  colour_hex?: string
  material?: string
  retailer: string
  price_inr?: number
  buy_url: string
  product_image_url: string
  vibe_tags?: string[]
  score: number
  explanation: string
}

export interface RecommendationsResponse {
  job_id: string
  total: number
  frames: Frame[]
}

export interface GenerateResponse {
  task_id: string
  status: string
  generations_remaining: number
}

export interface GenerateStatusResponse {
  task_id: string
  status: 'queued' | 'processing' | 'complete' | 'failed'
  image_url?: string
  expires_at?: string
  progress?: number
  error?: string
  message?: string
}

export interface SessionResponse {
  generations_used: number
  generations_remaining: number
  limit: number
}

export interface ApiError {
  error: string
  message: string
  generations_used?: number
  generations_remaining?: number
}

export interface CatalogueFrame {
  frame_id: string
  name: string
  style: string
  colour: string
  colour_hex?: string
  material?: string
  retailer: string
  price_inr?: number
  buy_url: string
  product_image_url: string
  vibe_tags?: string[]
}

export interface CatalogueResponse {
  frames: CatalogueFrame[]
  limit: number
  offset: number
  total: number
}
