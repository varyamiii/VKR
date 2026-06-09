-- ============================================================
-- Начальное заполнение БД для ВКР:
-- "Интеллектуальная система подготовки авиадиспетчеров
--  с использованием нейросетевых моделей"
--
-- PostgreSQL. Заполняются только справочные и учебные таблицы,
-- необходимые для запуска первой версии системы.
--
-- Не заполняются runtime-таблицы:
--   app.audio_generations,
--   app.test_attempts,
--   app.test_attempt_categories,
--   app.test_attempt_accents,
--   app.test_attempt_noise_profiles,
--   app.test_questions,
--   app.test_question_options.
-- Они должны наполняться во время работы приложения.
--
-- Фразы являются учебными примерами, составленными по типовым
-- шаблонам авиационной радиосвязи на основе открытых материалов FAA:
-- FAA AIM, FAA Order JO 7110.65 и Pilot/Controller Glossary.
-- ============================================================

BEGIN;

SET search_path TO app, public;

-- ------------------------------------------------------------
-- 1. Категории авиационных фраз
-- ------------------------------------------------------------

INSERT INTO app.phrase_categories (code, name_ru, name_en, description, is_active)
VALUES
    ('taxi', 'Руление', 'Taxi', 'Фразы, связанные с рулением воздушного судна по аэродрому.', TRUE),
    ('takeoff', 'Взлёт', 'Takeoff', 'Фразы, связанные с занятием ВПП и разрешением на взлёт.', TRUE),
    ('departure_climb', 'Вылет и набор высоты', 'Departure and climb', 'Фразы, используемые после вылета и при наборе высоты.', TRUE),
    ('approach', 'Заход на посадку', 'Approach', 'Фразы, связанные с заходом на посадку и наведением воздушного судна.', TRUE),
    ('landing', 'Посадка', 'Landing', 'Фразы, связанные с разрешением на посадку и действиями на финальном этапе.', TRUE),
    ('communication', 'Радиообмен', 'Communication', 'Краткие стандартные фразы радиообмена и подтверждения.', TRUE),
    ('emergency', 'Нестандартные и аварийные ситуации', 'Non-standard and emergency situations', 'Фразы, используемые при нестандартных ситуациях и необходимости повторения или отказа от выполнения команды.', TRUE)
ON CONFLICT (code) DO UPDATE SET
    name_ru = EXCLUDED.name_ru,
    name_en = EXCLUDED.name_en,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- ------------------------------------------------------------
-- 2. Акценты MeloTTS
-- ------------------------------------------------------------

INSERT INTO app.accents (code, name_ru, name_en, tts_language_code, tts_speaker_code, is_active)
VALUES
    ('en_us', 'Американский английский', 'American English', 'EN', 'EN-US', TRUE),
    ('en_br', 'Британский английский', 'British English', 'EN', 'EN-BR', TRUE),
    ('en_india', 'Индийский английский', 'Indian English', 'EN', 'EN_INDIA', TRUE)
ON CONFLICT (code) DO UPDATE SET
    name_ru = EXCLUDED.name_ru,
    name_en = EXCLUDED.name_en,
    tts_language_code = EXCLUDED.tts_language_code,
    tts_speaker_code = EXCLUDED.tts_speaker_code,
    is_active = EXCLUDED.is_active;

-- ------------------------------------------------------------
-- 3. Акустические условия и шумовые профили
-- ------------------------------------------------------------

INSERT INTO app.noise_profiles (code, name_ru, name_en, noise_type, file_path, default_snr_db, is_active)
VALUES
    ('none', 'Без шума', 'No noise', 'none', NULL, NULL, TRUE),
    ('engine_noise', 'Фоновый шум двигателя', 'Engine background noise', 'file', 'backend/static/noises/engine_noise.wav', 15.00, TRUE),
    ('radio_interference', 'Радиопомехи', 'Radio interference', 'file', 'backend/static/noises/radio_interference.wav', 12.00, TRUE)
ON CONFLICT (code) DO UPDATE SET
    name_ru = EXCLUDED.name_ru,
    name_en = EXCLUDED.name_en,
    noise_type = EXCLUDED.noise_type,
    file_path = EXCLUDED.file_path,
    default_snr_db = EXCLUDED.default_snr_db,
    is_active = EXCLUDED.is_active;

-- ------------------------------------------------------------
-- 4. Учебные авиационные фразы
-- ------------------------------------------------------------

WITH seed_phrases (
    category_code,
    phrase_text,
    phrase_template,
    example_text,
    role,
    difficulty_level,
    is_active
) AS (
    VALUES
    ('taxi', 'Taxi to runway two seven via alpha', 'Taxi to runway {runway} via {taxiway}', 'Taxi to runway two seven via alpha', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('taxi', 'Hold short of runway two seven', 'Hold short of runway {runway}', 'Hold short of runway two seven', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('taxi', 'Cross runway one eight at bravo', 'Cross runway {runway} at {taxiway}', 'Cross runway one eight at bravo', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),

    ('takeoff', 'Line up and wait runway two seven', 'Line up and wait runway {runway}', 'Line up and wait runway two seven', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('takeoff', 'Cleared for takeoff runway two seven', 'Cleared for takeoff runway {runway}', 'Cleared for takeoff runway two seven', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('takeoff', 'Cancel takeoff clearance', 'Cancel takeoff clearance', 'Cancel takeoff clearance', 'controller'::app.phrase_role, 'advanced'::app.difficulty_level, TRUE),

    ('departure_climb', 'Climb and maintain five thousand', 'Climb and maintain {altitude}', 'Climb and maintain five thousand', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('departure_climb', 'Turn left heading two seven zero', 'Turn left heading {heading}', 'Turn left heading two seven zero', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('departure_climb', 'Contact departure on one two four point three', 'Contact {unit} on {frequency}', 'Contact departure on one two four point three', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),
    ('departure_climb', 'Squawk four seven two one', 'Squawk {code}', 'Squawk four seven two one', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),

    ('approach', 'Descend and maintain three thousand', 'Descend and maintain {altitude}', 'Descend and maintain three thousand', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('approach', 'Cleared ILS approach runway two seven', 'Cleared {approach_type} approach runway {runway}', 'Cleared ILS approach runway two seven', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),
    ('approach', 'Report established on final', 'Report established on final', 'Report established on final', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),
    ('approach', 'Reduce speed to one six zero knots', 'Reduce speed to {speed} knots', 'Reduce speed to one six zero knots', 'controller'::app.phrase_role, 'intermediate'::app.difficulty_level, TRUE),

    ('landing', 'Cleared to land runway two seven', 'Cleared to land runway {runway}', 'Cleared to land runway two seven', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('landing', 'Go around', 'Go around', 'Go around', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('landing', 'Exit runway when able', 'Exit runway when able', 'Exit runway when able', 'controller'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),

    ('communication', 'Say again', 'Say again', 'Say again', 'both'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('communication', 'Stand by', 'Stand by', 'Stand by', 'both'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('communication', 'Roger', 'Roger', 'Roger', 'both'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),

    ('emergency', 'Unable', 'Unable', 'Unable', 'both'::app.phrase_role, 'basic'::app.difficulty_level, TRUE),
    ('emergency', 'Mayday mayday mayday', 'Mayday mayday mayday', 'Mayday mayday mayday', 'pilot'::app.phrase_role, 'advanced'::app.difficulty_level, TRUE),
    ('emergency', 'Pan pan pan pan pan pan', 'Pan pan pan pan pan pan', 'Pan pan pan pan pan pan', 'pilot'::app.phrase_role, 'advanced'::app.difficulty_level, TRUE),
    ('emergency', 'Minimum fuel', 'Minimum fuel', 'Minimum fuel', 'pilot'::app.phrase_role, 'advanced'::app.difficulty_level, TRUE)
)
INSERT INTO app.aviation_phrases (
    category_id,
    phrase_text,
    phrase_template,
    example_text,
    role,
    difficulty_level,
    is_active
)
SELECT
    c.id,
    s.phrase_text,
    s.phrase_template,
    s.example_text,
    s.role,
    s.difficulty_level,
    s.is_active
FROM seed_phrases s
JOIN app.phrase_categories c ON c.code = s.category_code
ON CONFLICT (category_id, phrase_text) DO UPDATE SET
    phrase_template = EXCLUDED.phrase_template,
    example_text = EXCLUDED.example_text,
    role = EXCLUDED.role,
    difficulty_level = EXCLUDED.difficulty_level,
    is_active = EXCLUDED.is_active;

-- ------------------------------------------------------------
-- 5. Варианты ответов для тестирования с выбором ответа
-- ------------------------------------------------------------

WITH seed_options (
    category_code,
    phrase_text,
    option_text,
    is_correct,
    is_active
) AS (
    VALUES
    ('taxi', 'Taxi to runway two seven via alpha', 'Taxi to runway two seven via alpha', TRUE, TRUE),
    ('taxi', 'Taxi to runway two seven via alpha', 'Taxi to runway one eight via bravo', FALSE, TRUE),
    ('taxi', 'Taxi to runway two seven via alpha', 'Hold short of runway two seven', FALSE, TRUE),
    ('taxi', 'Taxi to runway two seven via alpha', 'Cross runway two seven at alpha', FALSE, TRUE),

    ('taxi', 'Hold short of runway two seven', 'Hold short of runway two seven', TRUE, TRUE),
    ('taxi', 'Hold short of runway two seven', 'Cross runway two seven', FALSE, TRUE),
    ('taxi', 'Hold short of runway two seven', 'Taxi to runway two seven', FALSE, TRUE),
    ('taxi', 'Hold short of runway two seven', 'Line up and wait runway two seven', FALSE, TRUE),

    ('taxi', 'Cross runway one eight at bravo', 'Cross runway one eight at bravo', TRUE, TRUE),
    ('taxi', 'Cross runway one eight at bravo', 'Hold short of runway one eight at bravo', FALSE, TRUE),
    ('taxi', 'Cross runway one eight at bravo', 'Cross runway two seven at alpha', FALSE, TRUE),
    ('taxi', 'Cross runway one eight at bravo', 'Taxi to runway one eight via bravo', FALSE, TRUE),

    ('takeoff', 'Line up and wait runway two seven', 'Line up and wait runway two seven', TRUE, TRUE),
    ('takeoff', 'Line up and wait runway two seven', 'Cleared for takeoff runway two seven', FALSE, TRUE),
    ('takeoff', 'Line up and wait runway two seven', 'Hold short of runway two seven', FALSE, TRUE),
    ('takeoff', 'Line up and wait runway two seven', 'Exit runway when able', FALSE, TRUE),

    ('takeoff', 'Cleared for takeoff runway two seven', 'Cleared for takeoff runway two seven', TRUE, TRUE),
    ('takeoff', 'Cleared for takeoff runway two seven', 'Cleared to land runway two seven', FALSE, TRUE),
    ('takeoff', 'Cleared for takeoff runway two seven', 'Line up and wait runway two seven', FALSE, TRUE),
    ('takeoff', 'Cleared for takeoff runway two seven', 'Cancel takeoff clearance', FALSE, TRUE),

    ('takeoff', 'Cancel takeoff clearance', 'Cancel takeoff clearance', TRUE, TRUE),
    ('takeoff', 'Cancel takeoff clearance', 'Cleared for takeoff runway two seven', FALSE, TRUE),
    ('takeoff', 'Cancel takeoff clearance', 'Continue takeoff clearance', FALSE, TRUE),
    ('takeoff', 'Cancel takeoff clearance', 'Contact departure on one two four point three', FALSE, TRUE),

    ('departure_climb', 'Climb and maintain five thousand', 'Climb and maintain five thousand', TRUE, TRUE),
    ('departure_climb', 'Climb and maintain five thousand', 'Descend and maintain five thousand', FALSE, TRUE),
    ('departure_climb', 'Climb and maintain five thousand', 'Climb and maintain three thousand', FALSE, TRUE),
    ('departure_climb', 'Climb and maintain five thousand', 'Maintain present heading', FALSE, TRUE),

    ('departure_climb', 'Turn left heading two seven zero', 'Turn left heading two seven zero', TRUE, TRUE),
    ('departure_climb', 'Turn left heading two seven zero', 'Turn right heading two seven zero', FALSE, TRUE),
    ('departure_climb', 'Turn left heading two seven zero', 'Turn left heading one eight zero', FALSE, TRUE),
    ('departure_climb', 'Turn left heading two seven zero', 'Maintain present heading', FALSE, TRUE),

    ('departure_climb', 'Contact departure on one two four point three', 'Contact departure on one two four point three', TRUE, TRUE),
    ('departure_climb', 'Contact departure on one two four point three', 'Contact tower on one one eight point seven', FALSE, TRUE),
    ('departure_climb', 'Contact departure on one two four point three', 'Contact ground on one two one point nine', FALSE, TRUE),
    ('departure_climb', 'Contact departure on one two four point three', 'Squawk four seven two one', FALSE, TRUE),

    ('departure_climb', 'Squawk four seven two one', 'Squawk four seven two one', TRUE, TRUE),
    ('departure_climb', 'Squawk four seven two one', 'Squawk seven four two one', FALSE, TRUE),
    ('departure_climb', 'Squawk four seven two one', 'Contact departure on one two four point three', FALSE, TRUE),
    ('departure_climb', 'Squawk four seven two one', 'Ident', FALSE, TRUE),

    ('approach', 'Descend and maintain three thousand', 'Descend and maintain three thousand', TRUE, TRUE),
    ('approach', 'Descend and maintain three thousand', 'Climb and maintain three thousand', FALSE, TRUE),
    ('approach', 'Descend and maintain three thousand', 'Descend and maintain five thousand', FALSE, TRUE),
    ('approach', 'Descend and maintain three thousand', 'Reduce speed to one six zero knots', FALSE, TRUE),

    ('approach', 'Cleared ILS approach runway two seven', 'Cleared ILS approach runway two seven', TRUE, TRUE),
    ('approach', 'Cleared ILS approach runway two seven', 'Cleared visual approach runway two seven', FALSE, TRUE),
    ('approach', 'Cleared ILS approach runway two seven', 'Cleared for takeoff runway two seven', FALSE, TRUE),
    ('approach', 'Cleared ILS approach runway two seven', 'Report established on final', FALSE, TRUE),

    ('approach', 'Report established on final', 'Report established on final', TRUE, TRUE),
    ('approach', 'Report established on final', 'Report runway in sight', FALSE, TRUE),
    ('approach', 'Report established on final', 'Report leaving three thousand', FALSE, TRUE),
    ('approach', 'Report established on final', 'Contact tower on one one eight point seven', FALSE, TRUE),

    ('approach', 'Reduce speed to one six zero knots', 'Reduce speed to one six zero knots', TRUE, TRUE),
    ('approach', 'Reduce speed to one six zero knots', 'Increase speed to one six zero knots', FALSE, TRUE),
    ('approach', 'Reduce speed to one six zero knots', 'Reduce speed to two one zero knots', FALSE, TRUE),
    ('approach', 'Reduce speed to one six zero knots', 'Maintain present speed', FALSE, TRUE),

    ('landing', 'Cleared to land runway two seven', 'Cleared to land runway two seven', TRUE, TRUE),
    ('landing', 'Cleared to land runway two seven', 'Cleared for takeoff runway two seven', FALSE, TRUE),
    ('landing', 'Cleared to land runway two seven', 'Line up and wait runway two seven', FALSE, TRUE),
    ('landing', 'Cleared to land runway two seven', 'Go around', FALSE, TRUE),

    ('landing', 'Go around', 'Go around', TRUE, TRUE),
    ('landing', 'Go around', 'Cleared to land', FALSE, TRUE),
    ('landing', 'Go around', 'Exit runway when able', FALSE, TRUE),
    ('landing', 'Go around', 'Continue approach', FALSE, TRUE),

    ('landing', 'Exit runway when able', 'Exit runway when able', TRUE, TRUE),
    ('landing', 'Exit runway when able', 'Hold short of runway two seven', FALSE, TRUE),
    ('landing', 'Exit runway when able', 'Line up and wait runway two seven', FALSE, TRUE),
    ('landing', 'Exit runway when able', 'Cleared to land runway two seven', FALSE, TRUE),

    ('communication', 'Say again', 'Say again', TRUE, TRUE),
    ('communication', 'Say again', 'Stand by', FALSE, TRUE),
    ('communication', 'Say again', 'Roger', FALSE, TRUE),
    ('communication', 'Say again', 'Wilco', FALSE, TRUE),

    ('communication', 'Stand by', 'Stand by', TRUE, TRUE),
    ('communication', 'Stand by', 'Say again', FALSE, TRUE),
    ('communication', 'Stand by', 'Roger', FALSE, TRUE),
    ('communication', 'Stand by', 'Unable', FALSE, TRUE),

    ('communication', 'Roger', 'Roger', TRUE, TRUE),
    ('communication', 'Roger', 'Say again', FALSE, TRUE),
    ('communication', 'Roger', 'Stand by', FALSE, TRUE),
    ('communication', 'Roger', 'Unable', FALSE, TRUE),

    ('emergency', 'Unable', 'Unable', TRUE, TRUE),
    ('emergency', 'Unable', 'Roger', FALSE, TRUE),
    ('emergency', 'Unable', 'Wilco', FALSE, TRUE),
    ('emergency', 'Unable', 'Stand by', FALSE, TRUE),

    ('emergency', 'Mayday mayday mayday', 'Mayday mayday mayday', TRUE, TRUE),
    ('emergency', 'Mayday mayday mayday', 'Pan pan pan pan pan pan', FALSE, TRUE),
    ('emergency', 'Mayday mayday mayday', 'Minimum fuel', FALSE, TRUE),
    ('emergency', 'Mayday mayday mayday', 'Say again', FALSE, TRUE),

    ('emergency', 'Pan pan pan pan pan pan', 'Pan pan pan pan pan pan', TRUE, TRUE),
    ('emergency', 'Pan pan pan pan pan pan', 'Mayday mayday mayday', FALSE, TRUE),
    ('emergency', 'Pan pan pan pan pan pan', 'Minimum fuel', FALSE, TRUE),
    ('emergency', 'Pan pan pan pan pan pan', 'Unable', FALSE, TRUE),

    ('emergency', 'Minimum fuel', 'Minimum fuel', TRUE, TRUE),
    ('emergency', 'Minimum fuel', 'Mayday mayday mayday', FALSE, TRUE),
    ('emergency', 'Minimum fuel', 'Pan pan pan pan pan pan', FALSE, TRUE),
    ('emergency', 'Minimum fuel', 'Roger', FALSE, TRUE)
)
INSERT INTO app.answer_options (phrase_id, option_text, is_correct, is_active)
SELECT
    p.id,
    s.option_text,
    s.is_correct,
    s.is_active
FROM seed_options s
JOIN app.phrase_categories c ON c.code = s.category_code
JOIN app.aviation_phrases p
    ON p.category_id = c.id
   AND p.phrase_text = s.phrase_text
ON CONFLICT (phrase_id, option_text) DO UPDATE SET
    is_correct = EXCLUDED.is_correct,
    is_active = EXCLUDED.is_active;

COMMIT;
