# UK Tax Planner — production container.
# Zero lock-in by design: this same image runs on Railway, Render, Fly.io,
# Azure, or any Docker host (architecture doc §3, Hosting).

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint's native rendering libraries (Pango/cairo/GDK-PixBuf).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
        shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static at build time (WhiteNoise serves them at runtime).
# Dummy env values: settings only need them importable here, no DB access.
RUN SECRET_KEY=build-time-only DATABASE_URL=postgres://x:x@localhost/x \
    python manage.py collectstatic --noinput

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Bind to $PORT when the host provides one (Render, Railway, Fly all inject it),
# falling back to 8000 for local/compose. Worker count is WEB_CONCURRENCY
# (default 2) so a small/free instance can run 1 worker to stay within memory;
# 120s timeout gives WeasyPrint room to render a PDF on a low-CPU instance.
# Shell form so the ${...} vars expand at runtime.
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 120"]
