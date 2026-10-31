import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import properties, images, scripts, storyboards, videos, samples, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_property_video_generator")

app = FastAPI(
    title="AI Property Video Generator API",
    description="Automated AI and multimedia rendering pipeline converting property details and photos into promotional MP4 videos.",
    version="1.0.0"
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    # Return user-friendly error without leaking sensitive internals
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred while processing your request. Please try again."}
    )

# Register API Routers
app.include_router(health.router)
app.include_router(properties.router)
app.include_router(images.router)
app.include_router(scripts.router)
app.include_router(storyboards.router)
app.include_router(videos.router)
app.include_router(samples.router)

@app.get("/")
def root():
    return {
        "service": "AI Property Video Generator",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

# Wrap the complete FastAPI app so CORS headers are also included on errors
# produced by the ASGI exception handler or by an unhandled route exception.
app = CORSMiddleware(
    app=app,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
