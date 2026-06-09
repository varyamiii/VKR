import random
from collections import defaultdict

import psycopg

from app.core.config import get_settings
from app.services.generation_service import generate_audio_for_phrase
from app.services.report_service import build_pdf_report


def _planned_values(values: list[int], count: int) -> list[int]:
    shuffled = values[:]
    random.shuffle(shuffled)
    if len(shuffled) >= count:
        return shuffled[:count]
    result = shuffled[:]
    while len(result) < count:
        result.append(random.choice(values))
    random.shuffle(result)
    return result


def _load_phrases_by_category(conn: psycopg.Connection, category_ids: list[int]) -> dict[int, list[dict]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, category_id, phrase_text, example_text
            FROM app.aviation_phrases
            WHERE is_active = TRUE AND category_id = ANY(%s)
            ORDER BY id;
            """,
            (category_ids,),
        )
        rows = cur.fetchall()

    result: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        result[int(row["category_id"])].append(dict(row))
    return result


def _load_answer_options(conn: psycopg.Connection, phrase_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, option_text, is_correct
            FROM app.answer_options
            WHERE phrase_id = %s AND is_active = TRUE
            ORDER BY id;
            """,
            (phrase_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    if len(rows) < 4:
        raise ValueError(f"Для фразы id={phrase_id} должно быть не менее 4 вариантов ответа")
    correct = [row for row in rows if row["is_correct"]]
    if len(correct) != 1:
        raise ValueError(f"Для фразы id={phrase_id} должен быть ровно один корректный вариант ответа")
    incorrect = [row for row in rows if not row["is_correct"]]
    selected = [correct[0]] + random.sample(incorrect, 3)
    random.shuffle(selected)
    return selected



def ensure_student_owns_attempt(conn: psycopg.Connection, *, attempt_id: int, student_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM app.test_attempts
            WHERE id = %s AND student_id = %s;
            """,
            (attempt_id, student_id),
        )
        if not cur.fetchone():
            raise ValueError("Тестовая попытка не найдена или недоступна текущему ученику")

def create_test_attempt(
    conn: psycopg.Connection,
    *,
    student_id: int,
    test_type: str,
    category_ids: list[int],
    accent_ids: list[int],
    noise_profile_ids: list[int],
    questions_count: int | None = None,
) -> int:
    settings = get_settings()
    questions_count = questions_count or settings.default_questions_count

    phrases_by_category = _load_phrases_by_category(conn, category_ids)
    for category_id in category_ids:
        if not phrases_by_category.get(category_id):
            raise ValueError(f"В категории id={category_id} нет активных фраз")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app.test_attempts (student_id, test_type, questions_count)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (student_id, test_type, questions_count),
        )
        attempt_id = int(cur.fetchone()["id"])

        cur.executemany(
            "INSERT INTO app.test_attempt_categories (test_attempt_id, category_id) VALUES (%s, %s);",
            [(attempt_id, value) for value in category_ids],
        )
        cur.executemany(
            "INSERT INTO app.test_attempt_accents (test_attempt_id, accent_id) VALUES (%s, %s);",
            [(attempt_id, value) for value in accent_ids],
        )
        cur.executemany(
            "INSERT INTO app.test_attempt_noise_profiles (test_attempt_id, noise_profile_id) VALUES (%s, %s);",
            [(attempt_id, value) for value in noise_profile_ids],
        )

    category_plan = _planned_values(category_ids, questions_count)
    accent_plan = _planned_values(accent_ids, questions_count)
    noise_plan = _planned_values(noise_profile_ids, questions_count)

    for index in range(questions_count):
        category_id = category_plan[index]
        phrase = random.choice(phrases_by_category[category_id])
        accent_id = accent_plan[index]
        noise_profile_id = noise_plan[index]

        audio_data = generate_audio_for_phrase(
            conn,
            phrase_id=phrase["id"],
            accent_id=accent_id,
            noise_profile_id=noise_profile_id,
            speed=settings.default_speed,
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.test_questions (
                    test_attempt_id,
                    question_number,
                    phrase_id,
                    accent_id,
                    noise_profile_id,
                    audio_generation_id,
                    correct_answer_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    attempt_id,
                    index + 1,
                    phrase["id"],
                    accent_id,
                    noise_profile_id,
                    audio_data["audio_generation_id"],
                    phrase["phrase_text"],
                ),
            )
            question_id = int(cur.fetchone()["id"])

            if test_type == "choice":
                options = _load_answer_options(conn, phrase["id"])
                for order, option in enumerate(options, start=1):
                    cur.execute(
                        """
                        INSERT INTO app.test_question_options (
                            test_question_id,
                            answer_option_id,
                            option_order
                        )
                        VALUES (%s, %s, %s);
                        """,
                        (question_id, option["id"], order),
                    )

    return attempt_id


def get_test_state(conn: psycopg.Connection, attempt_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                test_type::text AS test_type,
                questions_count,
                correct_answers_count,
                score_percent,
                report_file_path,
                finished_at
            FROM app.test_attempts
            WHERE id = %s;
            """,
            (attempt_id,),
        )
        session = cur.fetchone()
        if not session:
            raise ValueError("Тестовая сессия не найдена")

        cur.execute(
            """
            SELECT
                q.id,
                q.question_number,
                q.correct_answer_text,
                q.user_answer_text,
                q.selected_answer_option_id,
                q.is_correct,
                ag.audio_file_path AS audio_url
            FROM app.test_questions q
            LEFT JOIN app.audio_generations ag ON ag.id = q.audio_generation_id
            WHERE q.test_attempt_id = %s
            ORDER BY q.question_number;
            """,
            (attempt_id,),
        )
        questions = [dict(row) for row in cur.fetchall()]

        question_ids = [q["id"] for q in questions]
        options_by_question: dict[int, list[dict]] = defaultdict(list)
        if question_ids:
            cur.execute(
                """
                SELECT
                    tqo.test_question_id,
                    ao.id AS answer_option_id,
                    ao.option_text,
                    tqo.option_order
                FROM app.test_question_options tqo
                JOIN app.answer_options ao ON ao.id = tqo.answer_option_id
                WHERE tqo.test_question_id = ANY(%s)
                ORDER BY tqo.test_question_id, tqo.option_order;
                """,
                (question_ids,),
            )
            for row in cur.fetchall():
                options_by_question[int(row["test_question_id"])].append(
                    {
                        "answer_option_id": row["answer_option_id"],
                        "option_text": row["option_text"],
                        "option_order": row["option_order"],
                    }
                )

    for question in questions:
        question["options"] = options_by_question.get(int(question["id"]), [])

    return {"session": dict(session), "questions": questions}


def submit_answer(
    conn: psycopg.Connection,
    *,
    attempt_id: int,
    question_id: int,
    answer_option_id: int | None = None,
    user_answer_text: str | None = None,
) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                q.id,
                q.correct_answer_text,
                s.test_type::text AS test_type
            FROM app.test_questions q
            JOIN app.test_attempts s ON s.id = q.test_attempt_id
            WHERE q.id = %s AND q.test_attempt_id = %s;
            """,
            (question_id, attempt_id),
        )
        question = cur.fetchone()
        if not question:
            raise ValueError("Вопрос не найден")

        if question["test_type"] == "choice":
            if answer_option_id is None:
                raise ValueError("Не выбран вариант ответа")
            cur.execute(
                """
                SELECT ao.is_correct
                FROM app.test_question_options tqo
                JOIN app.answer_options ao ON ao.id = tqo.answer_option_id
                WHERE tqo.test_question_id = %s AND ao.id = %s;
                """,
                (question_id, answer_option_id),
            )
            option = cur.fetchone()
            if not option:
                raise ValueError("Выбранный вариант не относится к данному вопросу")
            is_correct = bool(option["is_correct"])
            cur.execute(
                """
                UPDATE app.test_questions
                SET selected_answer_option_id = %s,
                    user_answer_text = NULL,
                    is_correct = %s
                WHERE id = %s;
                """,
                (answer_option_id, is_correct, question_id),
            )
        else:
            user_answer = (user_answer_text or "").strip()
            is_correct = user_answer.lower() == str(question["correct_answer_text"]).strip().lower()
            cur.execute(
                """
                UPDATE app.test_questions
                SET user_answer_text = %s,
                    selected_answer_option_id = NULL,
                    is_correct = %s
                WHERE id = %s;
                """,
                (user_answer, is_correct, question_id),
            )

    return is_correct


def finish_test(conn: psycopg.Connection, attempt_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE is_correct IS TRUE) AS correct,
                COUNT(*) FILTER (WHERE is_correct IS NOT NULL) AS answered
            FROM app.test_questions
            WHERE test_attempt_id = %s;
            """,
            (attempt_id,),
        )
        stats = cur.fetchone()
        total = int(stats["total"])
        answered = int(stats["answered"])
        correct = int(stats["correct"])
        if answered < total:
            raise ValueError("Нельзя завершить тест: отвечены не все вопросы")

        score = round((correct / total) * 100, 2) if total else 0.0
        cur.execute(
            """
            UPDATE app.test_attempts
            SET correct_answers_count = %s,
                score_percent = %s,
                finished_at = COALESCE(finished_at, now())
            WHERE id = %s;
            """,
            (correct, score, attempt_id),
        )

    report_url = build_pdf_report(conn, attempt_id)
    return {
        "session_id": attempt_id,
        "attempt_id": attempt_id,
        "correct_answers_count": correct,
        "questions_count": total,
        "score_percent": score,
        "result_url": f"/test/{attempt_id}/result",
        "report_url": report_url,
    }


def get_test_result(conn: psycopg.Connection, attempt_id: int) -> dict:
    state = get_test_state(conn, attempt_id)
    return state
