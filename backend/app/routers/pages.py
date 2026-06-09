from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _context(request: Request, **extra):
    data = {"request": request, "user": get_current_user(request)}
    data.update(extra)
    return data


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    if user and user.get("role") == "student":
        return RedirectResponse(url="/training", status_code=303)
    if user and user.get("role") == "teacher":
        return RedirectResponse(url="/teacher/dashboard", status_code=303)
    return templates.TemplateResponse("index.html", _context(request))


@router.get("/login/student", response_class=HTMLResponse)
def student_login(request: Request):
    return templates.TemplateResponse("login.html", _context(request, role="student", title="Вход для ученика"))


@router.get("/login/teacher", response_class=HTMLResponse)
def teacher_login(request: Request):
    return templates.TemplateResponse("login.html", _context(request, role="teacher", title="Вход для преподавателя"))


@router.get("/training", response_class=HTMLResponse)
def training(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "student":
        return RedirectResponse(url="/login/student", status_code=303)
    return templates.TemplateResponse("training.html", _context(request))


@router.get("/test/setup", response_class=HTMLResponse)
def test_setup(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "student":
        return RedirectResponse(url="/login/student", status_code=303)
    return templates.TemplateResponse("test_setup.html", _context(request))


@router.get("/test/{attempt_id}/run", response_class=HTMLResponse)
def test_run(request: Request, attempt_id: int):
    user = get_current_user(request)
    if not user or user.get("role") != "student":
        return RedirectResponse(url="/login/student", status_code=303)
    return templates.TemplateResponse("test_run.html", _context(request, session_id=attempt_id, attempt_id=attempt_id))


@router.get("/test/{attempt_id}/result", response_class=HTMLResponse)
def test_result(request: Request, attempt_id: int):
    user = get_current_user(request)
    if not user or user.get("role") != "student":
        return RedirectResponse(url="/login/student", status_code=303)
    return templates.TemplateResponse("test_result.html", _context(request, session_id=attempt_id, attempt_id=attempt_id))


@router.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "teacher":
        return RedirectResponse(url="/login/teacher", status_code=303)
    return templates.TemplateResponse("teacher_dashboard.html", _context(request))
