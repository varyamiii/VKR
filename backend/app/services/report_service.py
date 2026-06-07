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


def build_pdf_report(conn: psycopg.Connection, session_id: int) -> str:
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"test_report_{session_id}.pdf"
    report_path = settings.reports_dir / report_filename

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                s.id,
                s.test_type::text AS test_type,
                s.questions_count,
                s.correct_answers_count,
                s.score_percent,
                s.started_at,
                s.finished_at
            FROM app.test_sessions s
            WHERE s.id = %s;
            """,
            (session_id,),
        )
        session = cur.fetchone()
        if not session:
            raise ValueError("Тестовая сессия не найдена")

        cur.execute(
            """
            SELECT c.name_ru
            FROM app.test_session_categories sc
            JOIN app.phrase_categories c ON c.id = sc.category_id
            WHERE sc.test_session_id = %s
            ORDER BY c.name_ru;
            """,
            (session_id,),
        )
        categories = [row["name_ru"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT a.name_ru
            FROM app.test_session_accents sa
            JOIN app.accents a ON a.id = sa.accent_id
            WHERE sa.test_session_id = %s
            ORDER BY a.name_ru;
            """,
            (session_id,),
        )
        accents = [row["name_ru"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT n.name_ru
            FROM app.test_session_noise_profiles sn
            JOIN app.noise_profiles n ON n.id = sn.noise_profile_id
            WHERE sn.test_session_id = %s
            ORDER BY n.name_ru;
            """,
            (session_id,),
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
            WHERE q.test_session_id = %s
            ORDER BY q.question_number;
            """,
            (session_id,),
        )
        questions = list(cur.fetchall())

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
        Paragraph(f"Номер тестовой сессии: {session['id']}", normal),
        Paragraph(f"Тип теста: {session['test_type']}", normal),
        Paragraph(f"Категории: {', '.join(categories) if categories else '-'}", normal),
        Paragraph(f"Акценты: {', '.join(accents) if accents else '-'}", normal),
        Paragraph(f"Акустические условия: {', '.join(noises) if noises else '-'}", normal),
        Paragraph(f"Количество вопросов: {session['questions_count']}", normal),
        Paragraph(f"Правильных ответов: {session['correct_answers_count']}", normal),
        Paragraph(f"Итоговый результат: {session['score_percent']}%", normal),
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
            UPDATE app.test_sessions
            SET report_file_path = %s
            WHERE id = %s;
            """,
            (public_path, session_id),
        )

    return public_path
