from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import health, pair, choice, stats, image, gallery, state, portfolio, reset, upload

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
app.include_router(pair.router, prefix=settings.api_prefix, tags=["pair"])
app.include_router(choice.router, prefix=settings.api_prefix, tags=["choice"])
app.include_router(stats.router, prefix=settings.api_prefix, tags=["stats"])
app.include_router(gallery.router, prefix=settings.api_prefix, tags=["gallery"])
app.include_router(state.router, prefix=settings.api_prefix, tags=["convergence"])
app.include_router(portfolio.router, prefix=settings.api_prefix, tags=["portfolio"])
app.include_router(reset.router, prefix=settings.api_prefix, tags=["reset"])
app.include_router(upload.router, prefix=settings.api_prefix, tags=["upload"])
app.include_router(image.router, prefix=settings.api_prefix, tags=["image"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Image Preference Picker API", "version": "1.0.0"}