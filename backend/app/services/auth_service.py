from typing import Literal

import psycopg
from fastapi import HTTPException, Request

from app.services.password_service import verify_password

UserRole = Literal["student", "teacher"]


def authenticate_user(conn: psycopg.Connection, *, role: UserRole, login: str, password: str) -> dict | None:
    table = "students" if role == "student" else "teachers"
    id_field = "id"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {id_field} AS id, login, password_hash, full_name, is_active
            FROM app.{table}
            WHERE login = %s;
            """,
            (login.strip(),),
        )
        user = cur.fetchone()
    if not user or not user["is_active"]:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {
        "id": int(user["id"]),
        "login": user["login"],
        "full_name": user["full_name"],
        "role": role,
    }


def login_session(request: Request, user: dict) -> None:
    request.session.clear()
    request.session["user"] = user


def logout_session(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request) -> dict | None:
    user = request.session.get("user")
    return user if isinstance(user, dict) else None


def require_role(request: Request, role: UserRole) -> dict:
    user = get_current_user(request)
    if not user or user.get("role") != role:
        raise HTTPException(status_code=401, detail="Необходимо выполнить вход")
    return user


def require_student(request: Request) -> dict:
    return require_role(request, "student")


def require_teacher(request: Request) -> dict:
    return require_role(request, "teacher")
