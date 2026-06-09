from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.routers import auth, catalogs, pages, teacher, tests, training

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, same_site="lax")
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(catalogs.router)
app.include_router(training.router)
app.include_router(tests.router)
app.include_router(teacher.router)


@app.get("/health")
def health():
    return {"status": "ok"}
