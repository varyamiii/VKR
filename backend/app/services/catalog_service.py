import psycopg


def list_categories(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, code, name_ru, name_en, description
            FROM app.phrase_categories
            WHERE is_active = TRUE
            ORDER BY name_ru;
            """
        )
        return list(cur.fetchall())


def list_accents(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, code, name_ru, name_en, tts_language_code, tts_speaker_code
            FROM app.accents
            WHERE is_active = TRUE
            ORDER BY id;
            """
        )
        return list(cur.fetchall())


def list_noise_profiles(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, code, name_ru, name_en, noise_type, file_path, default_snr_db
            FROM app.noise_profiles
            WHERE is_active = TRUE
            ORDER BY id;
            """
        )
        return list(cur.fetchall())


def list_phrases(conn: psycopg.Connection, category_id: int | None = None) -> list[dict]:
    params: list[object] = []
    where = "p.is_active = TRUE"
    if category_id is not None:
        where += " AND p.category_id = %s"
        params.append(category_id)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                p.id,
                p.category_id,
                c.name_ru AS category_name,
                p.phrase_text,
                p.example_text,
                p.role::text AS role,
                p.difficulty_level::text AS difficulty_level
            FROM app.aviation_phrases p
            JOIN app.phrase_categories c ON c.id = p.category_id
            WHERE {where}
            ORDER BY c.name_ru, p.phrase_text;
            """,
            params,
        )
        return list(cur.fetchall())


def get_phrase(conn: psycopg.Connection, phrase_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.*, c.name_ru AS category_name
            FROM app.aviation_phrases p
            JOIN app.phrase_categories c ON c.id = p.category_id
            WHERE p.id = %s AND p.is_active = TRUE;
            """,
            (phrase_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError("Фраза не найдена")
    return dict(row)


def get_accent(conn: psycopg.Connection, accent_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM app.accents
            WHERE id = %s AND is_active = TRUE;
            """,
            (accent_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError("Акцент не найден")
    return dict(row)


def get_noise_profile(conn: psycopg.Connection, noise_profile_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM app.noise_profiles
            WHERE id = %s AND is_active = TRUE;
            """,
            (noise_profile_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError("Профиль шума не найден")
    return dict(row)
