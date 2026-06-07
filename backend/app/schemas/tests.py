from typing import Literal

from pydantic import BaseModel, Field


class CreateTestSessionRequest(BaseModel):
    test_type: Literal["choice", "manual_input"]
    category_ids: list[int] = Field(min_length=1)
    accent_ids: list[int] = Field(min_length=1)
    noise_profile_ids: list[int] = Field(min_length=1)
    questions_count: int = Field(default=10, ge=1, le=10)


class CreateTestSessionResponse(BaseModel):
    session_id: int
    run_url: str


class SubmitAnswerRequest(BaseModel):
    answer_option_id: int | None = None
    user_answer_text: str | None = None


class SubmitAnswerResponse(BaseModel):
    question_id: int
    is_correct: bool


class FinishTestResponse(BaseModel):
    session_id: int
    correct_answers_count: int
    questions_count: int
    score_percent: float
    result_url: str
    report_url: str | None
