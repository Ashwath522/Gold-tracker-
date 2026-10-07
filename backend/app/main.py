from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base
from .config import settings
from .api.prices import router as prices_router
from .api.analysis import router as analysis_router
from .api.investments import router as investments_router
from .api.backtest import router as backtest_router
from .api.model_info import router as model_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables upon startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend (default ports 3000, 3001, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(prices_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(investments_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(model_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "provider": settings.GOLD_PRICE_PROVIDER,
        "timezone": settings.TIMEZONE
    }
