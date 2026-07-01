from pydantic import BaseModel, Field, HttpUrl
from typing import Literal
from uuid import UUID
from datetime import datetime


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    job_id: UUID
    status: Literal["processing"] = "processing"
    session_token: str  # Returned so cross-domain clients can store and send via X-Session-Token header


class UploadError(BaseModel):
    error: str
    message: str


# ── Analysis ──────────────────────────────────────────────────────────────────

FaceShape  = Literal["oval", "round", "square", "heart", "diamond", "oblong"]
Undertone  = Literal["warm", "cool", "neutral"]
SizeBand   = Literal["narrow", "standard", "wide"]
Jawline    = Literal["angular", "soft", "tapered"]
Cheekbones = Literal["high", "normal", "low"]
EyeSet     = Literal["close", "average", "wide"]
SkinDepth  = Literal["fair", "light", "medium", "olive", "deep"]


class AnalysisResult(BaseModel):
    job_id: UUID
    status: Literal["complete", "processing", "failed"]
    face_shape: FaceShape | None = None
    face_shape_label: str | None = None  # nuanced display: "Oval (leaning towards Square)"
    face_shape_confidence: float | None = Field(None, ge=0.0, le=1.0)
    face_shape_explanation: str | None = None
    jawline: Jawline | None = None
    cheekbones: Cheekbones | None = None
    eye_set: EyeSet | None = None
    undertone: Undertone | None = None
    undertone_confidence: float | None = Field(None, ge=0.0, le=1.0)
    undertone_hex: str | None = None
    skin_depth: SkinDepth | None = None
    size_band: SizeBand | None = None


# ── Recommendations ───────────────────────────────────────────────────────────

class FrameRecommendation(BaseModel):
    frame_id: UUID
    rank: int
    name: str
    style: str
    colour: str
    colour_hex: str | None = None
    material: str | None = None
    retailer: str
    price_inr: int | None = None
    buy_url: str
    product_image_url: str
    vibe_tags: list[str] = []
    score: float
    explanation: str


class RecommendationsResponse(BaseModel):
    job_id: UUID
    total: int
    frames: list[FrameRecommendation]


# ── Generation ────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    job_id: UUID
    frame_id: UUID


class GenerateResponse(BaseModel):
    task_id: UUID
    status: Literal["queued"]
    generations_remaining: int


class GenerateLimitError(BaseModel):
    error: Literal["generation_limit_reached"]
    message: str
    generations_used: int
    generations_remaining: int


class GenerationStatus(BaseModel):
    task_id: UUID
    status: Literal["complete", "processing", "failed", "queued"]
    image_url: str | None = None
    expires_at: datetime | None = None
    progress: float | None = Field(None, ge=0.0, le=1.0)
    error: str | None = None
    message: str | None = None


# ── Session ───────────────────────────────────────────────────────────────────

class SessionStatus(BaseModel):
    generations_used: int
    generations_remaining: int
    limit: int = 3
