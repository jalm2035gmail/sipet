import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.routers import auth, ml, reports, sipet, users
from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
MEDIA_DIR = BASE_DIR / "media"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    templates.env.globals["current_year"] = datetime.utcnow().year
    templates.env.globals["debug"] = settings.DEBUG
    templates.env.globals["app_name"] = settings.APP_NAME

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(ml.router, prefix="/api/v1/ml", tags=["ml"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(sipet.router, prefix="/api/v1/sipet", tags=["sipet"])

    def render(request: Request, template_name: str, **context):
        defaults = {
            "request": request,
            "description": f"{settings.APP_NAME} — módulo PWA para SIPET",
            "app_name": settings.APP_NAME,
            "debug": settings.DEBUG,
        }
        defaults.update(context)
        return templates.TemplateResponse(template_name, defaults)

    @app.get("/", include_in_schema=False)
    async def root(request: Request):
        return render(request, "pages/index.html")

    @app.get("/login", include_in_schema=False)
    async def login_page(request: Request):
        return render(request, "pages/login.html", description="Iniciar sesión")

    @app.get("/register", include_in_schema=False)
    async def register_page(request: Request):
        return render(request, "pages/register.html", description="Crear cuenta")

    @app.get("/offline", include_in_schema=False)
    async def offline_page(request: Request):
        return render(request, "pages/offline.html", description="Sin conexión")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    async def manifest_alias():
        return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")

    @app.get("/sw.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            STATIC_DIR / "js" / "sw.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(STATIC_DIR / "icons" / "favicon.ico")

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION, "env": settings.ENVIRONMENT}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
