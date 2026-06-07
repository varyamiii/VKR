from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/training", response_class=HTMLResponse)
def training(request: Request):
    return templates.TemplateResponse("training.html", {"request": request})


@router.get("/test/setup", response_class=HTMLResponse)
def test_setup(request: Request):
    return templates.TemplateResponse("test_setup.html", {"request": request})


@router.get("/test/{session_id}/run", response_class=HTMLResponse)
def test_run(request: Request, session_id: int):
    return templates.TemplateResponse("test_run.html", {"request": request, "session_id": session_id})


@router.get("/test/{session_id}/result", response_class=HTMLResponse)
def test_result(request: Request, session_id: int):
    return templates.TemplateResponse("test_result.html", {"request": request, "session_id": session_id})
