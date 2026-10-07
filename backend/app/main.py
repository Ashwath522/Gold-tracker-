import base64
import secrets
from fastapi import FastAPI, Request, Response
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

def _authorized(header: str | None) -> bool:
    if not header or not header.lower().startswith("basic "):
        return False
    try:
        user, _, pwd = base64.b64decode(header[6:]).decode("utf-8").partition(":")
    except Exception:
        return False
    ok_user = secrets.compare_digest(user.encode(), settings.APP_USERNAME.encode())
    ok_pwd = secrets.compare_digest(pwd.encode(), settings.APP_PASSWORD.encode())
    return ok_user and ok_pwd


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    """Opt-in HTTP Basic auth (enabled only when APP_USERNAME and APP_PASSWORD are set)."""
    if (
        settings.APP_USERNAME
        and settings.APP_PASSWORD
        and request.method != "OPTIONS"
        and request.url.path != "/api/health"
        and not _authorized(request.headers.get("authorization"))
    ):
        return Response(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Gold Tracker"'},
        )
    return await call_next(request)


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
