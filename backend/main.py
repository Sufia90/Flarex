from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import comparisons, experiments, fire_safety, flammability, hardware, mission_relevance, rankings, relationships, sources
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.api_prefix}/health")
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(experiments.router, prefix=settings.api_prefix)
app.include_router(hardware.router, prefix=settings.api_prefix)
app.include_router(relationships.router, prefix=settings.api_prefix)
app.include_router(comparisons.router, prefix=settings.api_prefix)
app.include_router(rankings.router, prefix=settings.api_prefix)
app.include_router(mission_relevance.router, prefix=settings.api_prefix)
app.include_router(fire_safety.router, prefix=settings.api_prefix)
app.include_router(sources.router, prefix=settings.api_prefix)
app.include_router(flammability.router, prefix=settings.api_prefix)
