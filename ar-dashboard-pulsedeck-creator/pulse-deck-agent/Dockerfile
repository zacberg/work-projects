# Pulse Deck Builder service — container image
# Build context = project root (so we can copy the template + builder).
FROM python:3.12-slim

WORKDIR /app

# deps
COPY service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# app + builder + template
COPY build_pulse.py ./build_pulse.py
COPY pulse_template.pptx ./pulse_template.pptx
COPY service/app.py ./service/app.py

ENV PULSE_TEMPLATE=/app/pulse_template.pptx
EXPOSE 8000
# Render/Railway set $PORT; default 8000 locally
CMD ["sh", "-c", "uvicorn service.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
