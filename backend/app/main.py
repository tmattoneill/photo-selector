from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import health, ingest, pair, choice, stats

app = FastAPI(
    title="Image Preference Picker API",
    description="API for image preference ranking application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(ingest.router, prefix=settings.api_prefix, tags=["ingest"])
app.include_router(pair.router, prefix=settings.api_prefix, tags=["pair"])
app.include_router(choice.router, prefix=settings.api_prefix, tags=["choice"])
app.include_router(stats.router, prefix=settings.api_prefix, tags=["stats"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Image Preference Picker API", "version": "1.0.0"}