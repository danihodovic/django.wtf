# syntax=docker/dockerfile:1.9
FROM python:3.12-slim AS build

ARG INSTALL_DEV=false

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  gcc \
  git \
  libpq-dev \
  locales \
  python3-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get update \
  && apt-get install -y --no-install-recommends nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON=/usr/local/bin/python3.12 \
  UV_PROJECT_ENVIRONMENT=/opt/venv \
  PATH=/opt/venv/bin:$PATH \
  PYTHONUNBUFFERED=1

WORKDIR /src

COPY pyproject.toml uv.lock /src/

RUN --mount=type=cache,target=/root/.cache \
  if [ "$INSTALL_DEV" = "true" ]; then uv sync --locked --no-install-project --group dev; else uv sync --locked --no-install-project --no-dev; fi

COPY django_wtf/theme/static_src/package.json django_wtf/theme/static_src/package-lock.json /src/django_wtf/theme/static_src/
RUN --mount=type=cache,target=/root/.npm npm --prefix /src/django_wtf/theme/static_src ci

COPY . /src

RUN --mount=type=cache,target=/root/.cache \
  if [ "$INSTALL_DEV" = "true" ]; then uv sync --locked --no-editable --group dev; else uv sync --locked --no-editable --no-dev; fi

RUN <<EOF
set -e
export DJANGO_SETTINGS_MODULE=config.settings.test DATABASE_URL=postgres://postgres:5432/postgres
export CELERY_BROKER_URL= REDIS_URL=redis://test

python manage.py tailwind build
EOF

RUN <<EOF
set -e
export DJANGO_SETTINGS_MODULE=config.settings.production DATABASE_URL=postgres://postgres:5432/postgres
export CELERY_BROKER_URL= REDIS_URL=redis://test
export DJANGO_SECRET_KEY=test DJANGO_ADMIN_URL=test
export DJANGO_AWS_ACCESS_KEY_ID= DJANGO_AWS_SECRET_ACCESS_KEY=
export DJANGO_AWS_STORAGE_BUCKET_NAME=
export MAILGUN_API_KEY= MAILGUN_DOMAIN=
export DJANGO_O11Y_METRICS_EXPORT_MIGRATIONS=false

python manage.py collectstatic --no-input --ignore allauth_ui/input.css
EOF

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq5 \
  locales \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/venv/bin:$PATH \
  PYTHONUNBUFFERED=1 \
  PYTHONBREAKPOINT=pudb.set_trace \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  DJANGO_O11Y_METRICS_MULTIPROC_BASE_DIR=/tmp/django-wtf-prom-multiproc \
  PROMETHEUS_MULTIPROC_DIR=/tmp/django-wtf-prom-multiproc

RUN groupadd -r -g 1000 django && \
  useradd -r -u 1000 -g django -d /app -s /sbin/nologin django

COPY --from=build --chown=django:django /opt/venv /opt/venv
COPY --from=build --chown=django:django /src /app

RUN mkdir -p /tmp/django-wtf-prom-multiproc && \
  chown -R django:django /tmp/django-wtf-prom-multiproc

USER django
WORKDIR /app

EXPOSE 80

CMD ["gunicorn", "-c", "config/gunicorn.py", "config.wsgi"]
