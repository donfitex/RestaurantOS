FROM python:3.13-slim AS wheels
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=wheels /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels
RUN groupadd --system app && useradd --system --gid app --home-dir /app app
COPY . .
RUN DJANGO_SETTINGS_MODULE=config.build python manage.py collectstatic --noinput && mkdir -p /app/media && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]
