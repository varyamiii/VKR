from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.db.session import get_connection
from app.services.auth_service import authenticate_user, login_session, logout_session

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    role: Literal["student", "teacher"]
    login: str
    password: str


class LoginResponse(BaseModel):
    redirect_url: str
    full_name: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    with get_connection() as conn:
        user = authenticate_user(conn, role=payload.role, login=payload.login, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    login_session(request, user)
    redirect_url = "/training" if payload.role == "student" else "/teacher/dashboard"
    return LoginResponse(redirect_url=redirect_url, full_name=user["full_name"], role=payload.role)


@router.get("/logout")
def logout(request: Request):
    logout_session(request)
    return RedirectResponse(url="/", status_code=303)
