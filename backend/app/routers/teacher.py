from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request

from app.db.session import get_connection
from app.services.auth_service import require_teacher
from app.services.teacher_report_service import build_group_pdf_report, build_group_report_data, get_groups

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/groups")
def groups(request: Request):
    require_teacher(request)
    with get_connection() as conn:
        return {"groups": get_groups(conn)}


@router.get("/report")
def report(
    request: Request,
    group_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    test_type: str | None = Query(default=None, pattern="^(choice|manual_input)$"),
):
    require_teacher(request)
    try:
        with get_connection() as conn:
            return build_group_report_data(
                conn,
                group_id=group_id,
                date_from=date_from,
                date_to=date_to,
                test_type=test_type,
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/report/pdf")
def report_pdf(
    request: Request,
    group_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    test_type: str | None = Query(default=None, pattern="^(choice|manual_input)$"),
):
    require_teacher(request)
    try:
        with get_connection() as conn:
            report_url = build_group_pdf_report(
                conn,
                group_id=group_id,
                date_from=date_from,
                date_to=date_to,
                test_type=test_type,
            )
            return {"report_url": report_url}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
