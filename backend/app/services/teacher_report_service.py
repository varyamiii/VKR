from datetime import date, datetime

import psycopg
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import get_settings
from app.services.report_service import _register_font


def get_groups(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, group_name
            FROM app.student_groups
            ORDER BY group_name;
            """
        )
        return [dict(row) for row in cur.fetchall()]


def _filters_sql(group_id: int | None, date_from: date | None, date_to: date | None, test_type: str | None):
    filters = ["ta.finished_at IS NOT NULL"]
    params = []
    if group_id:
        filters.append("g.id = %s")
        params.append(group_id)
    if date_from:
        filters.append("ta.started_at::date >= %s")
        params.append(date_from)
    if date_to:
        filters.append("ta.started_at::date <= %s")
        params.append(date_to)
    if test_type:
        filters.append("ta.test_type::text = %s")
        params.append(test_type)
    return " AND ".join(filters), params


def build_group_report_data(
    conn: psycopg.Connection,
    *,
    group_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    test_type: str | None = None,
) -> dict:
    where_sql, params = _filters_sql(group_id, date_from, date_to, test_type)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                COUNT(*) AS attempts_count,
                COALESCE(ROUND(AVG(ta.score_percent)::numeric, 2), 0) AS avg_score,
                COALESCE(MAX(ta.score_percent), 0) AS best_score,
                COALESCE(MIN(ta.score_percent), 0) AS min_score
            FROM app.test_attempts ta
            JOIN app.students s ON s.id = ta.student_id
            LEFT JOIN app.student_groups g ON g.id = s.group_id
            WHERE {where_sql};
            """,
            params,
        )
        summary = dict(cur.fetchone())

        cur.execute(
            f"""
            SELECT
                s.id AS student_id,
                s.full_name,
                s.login,
                g.group_name,
                COUNT(ta.id) AS attempts_count,
                ROUND(AVG(ta.score_percent)::numeric, 2) AS avg_score,
                MAX(ta.score_percent) AS best_score,
                MAX(ta.finished_at) AS last_attempt_at
            FROM app.test_attempts ta
            JOIN app.students s ON s.id = ta.student_id
            LEFT JOIN app.student_groups g ON g.id = s.group_id
            WHERE {where_sql}
            GROUP BY s.id, s.full_name, s.login, g.group_name
            ORDER BY g.group_name NULLS LAST, s.full_name;
            """,
            params,
        )
        students = [dict(row) for row in cur.fetchall()]

        cur.execute(
            f"""
            SELECT
                ta.id,
                ta.started_at,
                ta.finished_at,
                ta.test_type::text AS test_type,
                ta.questions_count,
                ta.correct_answers_count,
                ta.score_percent,
                s.full_name,
                g.group_name,
                COALESCE(string_agg(DISTINCT c.name_ru, ', '), '-') AS categories,
                COALESCE(string_agg(DISTINCT a.name_ru, ', '), '-') AS accents,
                COALESCE(string_agg(DISTINCT n.name_ru, ', '), '-') AS noises
            FROM app.test_attempts ta
            JOIN app.students s ON s.id = ta.student_id
            LEFT JOIN app.student_groups g ON g.id = s.group_id
            LEFT JOIN app.test_attempt_categories tac ON tac.test_attempt_id = ta.id
            LEFT JOIN app.phrase_categories c ON c.id = tac.category_id
            LEFT JOIN app.test_attempt_accents taa ON taa.test_attempt_id = ta.id
            LEFT JOIN app.accents a ON a.id = taa.accent_id
            LEFT JOIN app.test_attempt_noise_profiles tan ON tan.test_attempt_id = ta.id
            LEFT JOIN app.noise_profiles n ON n.id = tan.noise_profile_id
            WHERE {where_sql}
            GROUP BY ta.id, ta.started_at, ta.finished_at, ta.test_type, ta.questions_count,
                     ta.correct_answers_count, ta.score_percent, s.full_name, g.group_name
            ORDER BY ta.finished_at DESC, ta.id DESC
            LIMIT 300;
            """,
            params,
        )
        attempts = [dict(row) for row in cur.fetchall()]

    return {
        "filters": {
            "group_id": group_id,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "test_type": test_type,
        },
        "summary": summary,
        "students": students,
        "attempts": attempts,
    }


def build_group_pdf_report(conn: psycopg.Connection, **filters) -> str:
    data = build_group_report_data(conn, **filters)
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"group_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = settings.reports_dir / filename

    font_name, font_bold = _register_font()
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleRus", parent=styles["Title"], fontName=font_bold, fontSize=16, leading=20, alignment=1)
    normal = ParagraphStyle("NormalRus", parent=styles["Normal"], fontName=font_name, fontSize=9, leading=12)

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.2 * cm, leftMargin=1.2 * cm, topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    elements = [
        Paragraph("Сводный отчёт по результатам тестирования", title),
        Spacer(1, 12),
        Paragraph(f"Количество попыток: {data['summary']['attempts_count']}", normal),
        Paragraph(f"Средний результат: {data['summary']['avg_score']}%", normal),
        Paragraph(f"Лучший результат: {data['summary']['best_score']}%", normal),
        Paragraph(f"Минимальный результат: {data['summary']['min_score']}%", normal),
        Spacer(1, 12),
    ]

    student_table = [["Группа", "Ученик", "Попыток", "Средний %", "Лучший %"]]
    for row in data["students"]:
        student_table.append([
            row.get("group_name") or "-",
            Paragraph(row.get("full_name") or "-", normal),
            str(row.get("attempts_count") or 0),
            str(row.get("avg_score") or 0),
            str(row.get("best_score") or 0),
        ])

    table = Table(student_table, colWidths=[2.5 * cm, 7.0 * cm, 2.0 * cm, 2.5 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1F3A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#8AA4C5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF5FF")]),
    ]))
    elements.append(table)
    doc.build(elements)
    return f"/static/reports/{filename}"
