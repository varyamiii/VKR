from pathlib import Path

import psycopg
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import get_settings


def _register_font() -> tuple[str, str]:
    settings = get_settings()
    font_path = Path(settings.report_font_path)
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans", str(font_path)))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(font_path)))
        return "DejaVuSans", "DejaVuSans-Bold"
    return "Helvetica", "Helvetica-Bold"


def _styles():
    font_name, font_bold = _register_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName=font_bold,
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=18,
    )
    normal = ParagraphStyle(
        "NormalRus",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=13,
    )
    return font_name, font_bold, title_style, normal


def build_pdf_report(conn: psycopg.Connection, attempt_id: int) -> str:
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"test_report_{attempt_id}.pdf"
    report_path = settings.reports_dir / report_filename

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ta.id,
                ta.test_type::text AS test_type,
                ta.questions_count,
                ta.correct_answers_count,
                ta.score_percent,
                ta.started_at,
                ta.finished_at,
                s.full_name AS student_name,
                s.login AS student_login,
                g.group_name
            FROM app.test_attempts ta
            LEFT JOIN app.students s ON s.id = ta.student_id
            LEFT JOIN app.student_groups g ON g.id = s.group_id
            WHERE ta.id = %s;
            """,
            (attempt_id,),
        )
        attempt = cur.fetchone()
        if not attempt:
            raise ValueError("Тестовая попытка не найдена")

        cur.execute(
            """
            SELECT c.name_ru
            FROM app.test_attempt_categories tac
            JOIN app.phrase_categories c ON c.id = tac.category_id
            WHERE tac.test_attempt_id = %s
            ORDER BY c.name_ru;
            """,
            (attempt_id,),
        )
        categories = [row["name_ru"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT a.name_ru
            FROM app.test_attempt_accents taa
            JOIN app.accents a ON a.id = taa.accent_id
            WHERE taa.test_attempt_id = %s
            ORDER BY a.name_ru;
            """,
            (attempt_id,),
        )
        accents = [row["name_ru"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT n.name_ru
            FROM app.test_attempt_noise_profiles tan
            JOIN app.noise_profiles n ON n.id = tan.noise_profile_id
            WHERE tan.test_attempt_id = %s
            ORDER BY n.name_ru;
            """,
            (attempt_id,),
        )
        noises = [row["name_ru"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT
                q.question_number,
                q.correct_answer_text,
                COALESCE(q.user_answer_text, ao.option_text, '') AS user_answer,
                q.is_correct,
                a.name_ru AS accent_name,
                n.name_ru AS noise_name
            FROM app.test_questions q
            JOIN app.accents a ON a.id = q.accent_id
            JOIN app.noise_profiles n ON n.id = q.noise_profile_id
            LEFT JOIN app.answer_options ao ON ao.id = q.selected_answer_option_id
            WHERE q.test_attempt_id = %s
            ORDER BY q.question_number;
            """,
            (attempt_id,),
        )
        questions = list(cur.fetchall())

    font_name, _, title_style, normal = _styles()

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    elements = [
        Paragraph("Отчёт о прохождении тестирования", title_style),
        Paragraph(f"Номер попытки: {attempt['id']}", normal),
        Paragraph(f"Ученик: {attempt['student_name'] or '-'}", normal),
        Paragraph(f"Группа: {attempt['group_name'] or '-'}", normal),
        Paragraph(f"Тип теста: {attempt['test_type']}", normal),
        Paragraph(f"Категории: {', '.join(categories) if categories else '-'}", normal),
        Paragraph(f"Акценты: {', '.join(accents) if accents else '-'}", normal),
        Paragraph(f"Акустические условия: {', '.join(noises) if noises else '-'}", normal),
        Paragraph(f"Количество вопросов: {attempt['questions_count']}", normal),
        Paragraph(f"Правильных ответов: {attempt['correct_answers_count']}", normal),
        Paragraph(f"Итоговый результат: {attempt['score_percent']}%", normal),
        Spacer(1, 14),
    ]

    data = [["№", "Правильный ответ", "Ответ пользователя", "Результат"]]
    for q in questions:
        result = "Верно" if q["is_correct"] else "Неверно"
        data.append([
            str(q["question_number"]),
            Paragraph(str(q["correct_answer_text"]), normal),
            Paragraph(str(q["user_answer"]), normal),
            result,
        ])

    table = Table(data, colWidths=[1.0 * cm, 7.1 * cm, 6.6 * cm, 2.3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1F3A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#8AA4C5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF5FF")]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)

    public_path = f"/static/reports/{report_filename}"
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.test_attempts
            SET report_file_path = %s
            WHERE id = %s;
            """,
            (public_path, attempt_id),
        )

    return public_path
