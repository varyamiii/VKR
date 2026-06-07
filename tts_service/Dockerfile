# Важно: используется уже собранный локальный образ melotts,
# который у вас сейчас запускается командой docker run ... melotts.
FROM melotts

WORKDIR /app

COPY requirements.txt /tmp/tts_service_requirements.txt
RUN pip install --no-cache-dir -r /tmp/tts_service_requirements.txt

COPY app /app/app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
