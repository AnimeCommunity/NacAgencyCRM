FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .
RUN chown -R app:app /app

USER app
EXPOSE 8000

CMD ["gunicorn", "CRM.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]

