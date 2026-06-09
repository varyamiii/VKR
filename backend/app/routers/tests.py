from fastapi import APIRouter, HTTPException, Request

from app.db.session import get_connection
from app.schemas.tests import (
    CreateTestSessionRequest,
    CreateTestSessionResponse,
    FinishTestResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.auth_service import require_student
from app.services.test_service import (
    create_test_attempt,
    ensure_student_owns_attempt,
    finish_test,
    get_test_result,
    get_test_state,
    submit_answer,
)

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("", response_model=CreateTestSessionResponse)
def create_test(payload: CreateTestSessionRequest, request: Request):
    student = require_student(request)
    try:
        with get_connection() as conn:
            attempt_id = create_test_attempt(
                conn,
                student_id=int(student["id"]),
                test_type=payload.test_type,
                category_ids=payload.category_ids,
                accent_ids=payload.accent_ids,
                noise_profile_ids=payload.noise_profile_ids,
                questions_count=payload.questions_count,
            )
            return CreateTestSessionResponse(session_id=attempt_id, run_url=f"/test/{attempt_id}/run")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{attempt_id}/state")
def state(attempt_id: int, request: Request):
    student = require_student(request)
    try:
        with get_connection() as conn:
            ensure_student_owns_attempt(conn, attempt_id=attempt_id, student_id=int(student["id"]))
            return get_test_state(conn, attempt_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{attempt_id}/questions/{question_id}/answer", response_model=SubmitAnswerResponse)
def answer(attempt_id: int, question_id: int, payload: SubmitAnswerRequest, request: Request):
    student = require_student(request)
    try:
        with get_connection() as conn:
            ensure_student_owns_attempt(conn, attempt_id=attempt_id, student_id=int(student["id"]))
            is_correct = submit_answer(
                conn,
                attempt_id=attempt_id,
                question_id=question_id,
                answer_option_id=payload.answer_option_id,
                user_answer_text=payload.user_answer_text,
            )
            return SubmitAnswerResponse(question_id=question_id, is_correct=is_correct)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{attempt_id}/finish", response_model=FinishTestResponse)
def finish(attempt_id: int, request: Request):
    student = require_student(request)
    try:
        with get_connection() as conn:
            ensure_student_owns_attempt(conn, attempt_id=attempt_id, student_id=int(student["id"]))
            return finish_test(conn, attempt_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{attempt_id}/result")
def result(attempt_id: int, request: Request):
    student = require_student(request)
    try:
        with get_connection() as conn:
            ensure_student_owns_attempt(conn, attempt_id=attempt_id, student_id=int(student["id"]))
            return get_test_result(conn, attempt_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
