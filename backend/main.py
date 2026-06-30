from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import upload, analysis, recommendations, generate, catalogue
from config import settings

app = FastAPI(
    title="FrameAI API",
    version="1.0.0",
    description="AI-powered eyeglass frame recommendation engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, tags=["upload"])
app.include_router(analysis.router, tags=["analysis"])
app.include_router(recommendations.router, tags=["recommendations"])
app.include_router(generate.router, tags=["generate"])
app.include_router(catalogue.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
