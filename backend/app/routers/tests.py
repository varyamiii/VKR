from fastapi import APIRouter, HTTPException

from app.db.session import get_connection
from app.schemas.tests import (
    CreateTestSessionRequest,
    CreateTestSessionResponse,
    FinishTestResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.test_service import create_test_session, finish_test, get_test_result, get_test_state, submit_answer

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("", response_model=CreateTestSessionResponse)
def create_test(request: CreateTestSessionRequest):
    try:
        with get_connection() as conn:
            session_id = create_test_session(
                conn,
                test_type=request.test_type,
                category_ids=request.category_ids,
                accent_ids=request.accent_ids,
                noise_profile_ids=request.noise_profile_ids,
                questions_count=request.questions_count,
            )
            return CreateTestSessionResponse(session_id=session_id, run_url=f"/test/{session_id}/run")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{session_id}/state")
def state(session_id: int):
    try:
        with get_connection() as conn:
            return get_test_state(conn, session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/questions/{question_id}/answer", response_model=SubmitAnswerResponse)
def answer(session_id: int, question_id: int, request: SubmitAnswerRequest):
    try:
        with get_connection() as conn:
            is_correct = submit_answer(
                conn,
                session_id=session_id,
                question_id=question_id,
                answer_option_id=request.answer_option_id,
                user_answer_text=request.user_answer_text,
            )
            return SubmitAnswerResponse(question_id=question_id, is_correct=is_correct)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/finish", response_model=FinishTestResponse)
def finish(session_id: int):
    try:
        with get_connection() as conn:
            return finish_test(conn, session_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{session_id}/result")
def result(session_id: int):
    try:
        with get_connection() as conn:
            return get_test_result(conn, session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
