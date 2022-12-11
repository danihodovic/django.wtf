FROM python:3.10.8

RUN apt-get update && apt install -y locales \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment && \
	echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
	echo "LANG=en_US.UTF-8" > /etc/locale.conf && \
	locale-gen en_US.UTF-8

RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - && apt install -y nodejs #!COMMIT

WORKDIR /app/

# hadolint ignore=DL3013
RUN pip install pip poetry #!COMMIT
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction #!COMMIT

ENV PYTHONUNBUFFERED 1
ENV PYTHONBREAKPOINT pudb.set_trace

COPY django_apps/theme/static_src/package.json django_apps/theme/static_src/package-lock.json /app/django_apps/theme/static_src/
RUN cd /app/django_apps/theme/static_src && npm install

COPY . /app/
RUN DJANGO_SETTINGS_MODULE=config.settings.test \
	DATABASE_URL=postgres://postgres \
	CELERY_BROKER_URL=zar \
	REDIS_URL=bar \
	python manage.py tailwind install --no-input
RUN DJANGO_SETTINGS_MODULE=config.settings.test \
	DATABASE_URL=postgres://postgres \
	CELERY_BROKER_URL=zar \
	REDIS_URL=bar \
	python manage.py tailwind build --no-input

# Install the app itself so we can import from it
RUN poetry install --no-interaction

CMD ["gunicorn", "-b", "0.0.0.0:80", "config.wsgi", "--timeout", "90"]
