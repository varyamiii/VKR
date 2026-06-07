# ATC Speech Trainer

Веб-приложение для ВКР: генерация английских авиационных фраз с разными акцентами и акустическими условиями, учебный режим, тестирование и PDF-отчёт.

## 1. Состав проекта

```text
backend/       FastAPI backend, HTML/CSS/JS, работа с БД, наложение шумов, PDF-отчёты
tts_service/   отдельный HTTP-сервис-обёртка над MeloTTS
db/            SQL-скрипты создания и заполнения PostgreSQL
docs/          материалы и заметки по архитектуре
```

## 2. Что уже реализовано

1. Учебный режим:
   - загрузка категорий, фраз, акцентов и шумов из PostgreSQL;
   - генерация речи через MeloTTS;
   - наложение шума поверх сгенерированного WAV;
   - выдача аудио в интерфейс.

2. Тестовый режим:
   - выбор типа теста: варианты ответа или ручной ввод;
   - выбор категорий, акцентов и шумов;
   - формирование теста до 10 вопросов;
   - генерация аудио для каждого вопроса;
   - проверка ответов;
   - формирование PDF-отчёта.

3. Интерфейс:
   - тёмно-синяя цветовая схема;
   - страницы учебного режима, настройки теста, прохождения теста и результата.

## 3. Важные требования

На компьютере должны быть установлены:

- Docker Desktop;
- уже собранный локальный Docker-образ `melotts`;
- PostgreSQL, если используется ваша локальная БД.

Проверить наличие образа MeloTTS:

```powershell
docker images melotts
```

Если образ есть, `tts_service/Dockerfile` сможет использовать строку:

```dockerfile
FROM melotts
```

## 4. Куда положить файлы шумов

Положите свои готовые WAV-файлы сюда:

```text
backend/app/static/noises/engine_noise.wav
backend/app/static/noises/radio_interference.wav
```

Файлы должны называться именно так, потому что такие пути уже записаны в таблице `app.noise_profiles`:

```text
backend/static/noises/engine_noise.wav
backend/static/noises/radio_interference.wav
```

Если хотите использовать другие имена, измените поле `file_path` в таблице `app.noise_profiles`.

Логика обработки шума такая: система берёт длительность сгенерированной речи, затем обрезает файл шума до этой длительности и накладывает его поверх речи. Если шумовой файл вдруг окажется короче речи, он будет повторён и затем обрезан.

## 5. Запуск с уже созданной локальной PostgreSQL

Это основной вариант, так как база данных у вас уже создана и заполнена.

### Шаг 1. Распакуйте проект

Откройте папку проекта в VS Code.

### Шаг 2. Создайте `.env`

Скопируйте `.env.example` в `.env`:

```powershell
copy .env.example .env
```

Откройте `.env` и укажите свои данные PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@host.docker.internal:5432/vkr_atc_training
TTS_SERVICE_URL=http://tts_service:8001
MELO_LANGUAGE=EN
MELO_DEVICE=cpu
```

`host.docker.internal` нужен потому, что backend будет работать внутри Docker-контейнера, а PostgreSQL находится на Windows-хосте.

### Шаг 3. Положите шумы

```text
backend/app/static/noises/engine_noise.wav
backend/app/static/noises/radio_interference.wav
```

### Шаг 4. Запустите backend и MeloTTS service

```powershell
docker compose up --build
```

### Шаг 5. Откройте приложение

```text
http://localhost:8000
```

Проверка backend:

```text
http://localhost:8000/health
```

Проверка MeloTTS service:

```text
http://localhost:8001/health
```

## 6. Запуск с PostgreSQL внутри Docker

Если захотите запустить всё полностью в Docker, используйте дополнительный compose-файл:

```powershell
docker compose -f docker-compose.with-db.yml up --build
```

В этом варианте PostgreSQL поднимется в контейнере, а SQL-скрипты из папки `db/` будут выполнены автоматически при первом создании volume.

Если нужно пересоздать БД внутри Docker полностью:

```powershell
docker compose -f docker-compose.with-db.yml down -v
docker compose -f docker-compose.with-db.yml up --build
```

## 7. Если MeloTTS service не запускается

Проверьте, что локальный образ `melotts` существует:

```powershell
docker images melotts
```

Проверьте логи:

```powershell
docker compose logs -f tts_service
```

Если внутри образа `melotts` нет FastAPI/uvicorn, они будут установлены из `tts_service/requirements.txt` при сборке сервиса.

## 8. Если аудио не генерируется

Проверьте:

1. backend видит TTS-сервис:

```powershell
docker compose logs -f backend
```

2. TTS-сервис видит speaker-коды:

```text
http://localhost:8001/health
```

Ожидаемые speaker-коды:

```text
EN-US
EN-BR
EN_INDIA
```

3. В БД в таблице `app.accents` заполнены поля `tts_speaker_code`.

## 9. Если шум не накладывается

Проверьте, что файлы реально лежат здесь:

```text
backend/app/static/noises/engine_noise.wav
backend/app/static/noises/radio_interference.wav
```

Проверьте, что в БД указаны такие пути:

```sql
SELECT code, file_path FROM app.noise_profiles;
```

## 10. Основные страницы

```text
/                  главная страница
/training          учебный режим
/test/setup        настройка теста
/test/{id}/run     прохождение теста
/test/{id}/result  результат и PDF-отчёт
```

## 11. Основные API

```text
GET  /api/categories
GET  /api/accents
GET  /api/noise-profiles
GET  /api/phrases?category_id=1
POST /api/training/generate
POST /api/tests
GET  /api/tests/{session_id}/state
POST /api/tests/{session_id}/questions/{question_id}/answer
POST /api/tests/{session_id}/finish
GET  /api/tests/{session_id}/result
```
