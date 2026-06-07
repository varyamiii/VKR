from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import catalogs, pages, tests, training

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(pages.router)
app.include_router(catalogs.router)
app.include_router(training.router)
app.include_router(tests.router)


@app.get("/health")
def health():
    return {"status": "ok"}
