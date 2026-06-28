from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.analyze import router as analyze_router
from routes.health import router as health_router
from routes.stats import router as stats_router
from routes.explain import router as explain_router

app = FastAPI(title="ToS Reader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock down to chrome-extension://* in production
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(analyze_router)
app.include_router(health_router)
app.include_router(stats_router)
app.include_router(explain_router)
