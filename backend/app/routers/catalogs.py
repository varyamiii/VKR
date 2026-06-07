from fastapi import APIRouter, HTTPException, Query

from app.db.session import get_connection
from app.services.catalog_service import list_accents, list_categories, list_noise_profiles, list_phrases

router = APIRouter(prefix="/api", tags=["catalogs"])


@router.get("/categories")
def get_categories():
    with get_connection() as conn:
        return list_categories(conn)


@router.get("/accents")
def get_accents():
    with get_connection() as conn:
        return list_accents(conn)


@router.get("/noise-profiles")
def get_noise_profiles():
    with get_connection() as conn:
        return list_noise_profiles(conn)


@router.get("/phrases")
def get_phrases(category_id: int | None = Query(default=None, gt=0)):
    try:
        with get_connection() as conn:
            return list_phrases(conn, category_id=category_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
