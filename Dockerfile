# syntax=docker/dockerfile:1.3-labs
FROM python:3.11

# Base apt dependencies
RUN <<EOF
set -e
apt-get update && apt install -y locales

# Install postgresql-client-14
apt-get install -y lsb-release wget
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update
apt-get install -y postgresql-client-15
rm -rf /var/lib/apt/lists/*

curl -sL https://deb.nodesource.com/setup_20.x | bash - && apt install -y nodejs #!COMMIT

# Fix locales
echo "LC_ALL=en_US.UTF-8" >> /etc/environment
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
locale-gen en_US.UTF-8
EOF

WORKDIR /app/

# hadolint ignore=DL3013
RUN pip install pip poetry==1.4.2 #!COMMIT
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction #!COMMIT

ENV PYTHONUNBUFFERED 1
ENV PYTHONBREAKPOINT pudb.set_trace

COPY ptpython_config.py /root/.config/ptpython/config.py

COPY django_wtf/theme/static_src/package.json django_wtf/theme/static_src/package-lock.json /app/django_wtf/theme/static_src/
RUN cd /app/django_wtf/theme/static_src && npm install

COPY . /app/

RUN <<EOF
set -e
export DJANGO_SETTINGS_MODULE=config.settings.test DATABASE_URL=postgres://postgres:5432/postgres
export CELERY_BROKER_URL= REDIS_URL=

python manage.py tailwind build --no-input
EOF

RUN <<EOF
set -e
export DJANGO_SETTINGS_MODULE=config.settings.production DATABASE_URL=postgres://postgres:5432/postgres
export CELERY_BROKER_URL= REDIS_URL=
export DJANGO_SECRET_KEY=test DJANGO_ADMIN_URL=test
export DJANGO_AWS_ACCESS_KEY_ID= DJANGO_AWS_SECRET_ACCESS_KEY=
export DJANGO_AWS_STORAGE_BUCKET_NAME=
export MAILGUN_API_KEY= MAILGUN_DOMAIN=

python manage.py collectstatic --no-input
EOF

# Install the app itself so we can import from it
RUN poetry install --no-interaction

CMD ["gunicorn", "-b", "0.0.0.0:80", "config.wsgi", "--timeout", "90"]
