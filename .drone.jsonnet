local pipelineCommon = {
  kind: 'pipeline',
  type: 'docker',
};

local cacheCommon = {
  image: 'danihodovic/drone-cache',
  settings: {
    backend: 'filesystem',
    cache_key: '{{ .Repo.Name }}_{{ checksum "poetry.lock" }}',
    mount: [
      '.poetry',
      '.poetry-cache',
    ],
  },
  volumes: [{ name: 'cache', path: '/tmp/cache' }],
};

local restoreCache = cacheCommon {
  name: 'restore-python-cache',
  settings+: {
    restore: true,
  },
};
local rebuildCache = cacheCommon {
  name: 'rebuild-python-cache',
  depends_on: [
    'install-python-deps',
  ],
  settings+: {
    rebuild: true,
  },
};

local common = {
  depends_on: ['install-python-deps'],
  image: 'python:3.8',
  environment: {
    POETRY_CACHE_DIR: '/drone/src/.poetry-cache',
    POETRY_VIRTUALENVS_IN_PROJECT: 'false',
    DJANGO_SETTINGS_MODULE: 'config.settings.test',
    DATABASE_URL: 'postgres://postgres:postgres@postgres:5432/django-apps',
    CELERY_BROKER_URL: 'redis://redis:6379/0',
  },
  commands: [
    '. .poetry/env && . $(poetry env info -p)/bin/activate',
  ],
};

local pythonPipeline = pipelineCommon {
  name: 'python',
  trigger: {
    event: [
      'push',
    ],
  },
  volumes: [
    {
      name: 'cache',
      host: {
        path: '/tmp/drone-cache',
      },
    },
  ],
  services: [
    {
      name: 'postgres',
      image: 'postgres:14',
      environment: {
        POSTGRES_USER: 'postgres',
        POSTGRES_PASSWORD: 'postgres',
        POSTGRES_DB: 'django-apps',
      },
    },
    {
      name: 'redis',
      image: 'redis:6-alpine',
    },
  ],
  steps: [
    restoreCache,
    common {
      name: 'install-python-deps',
      depends_on: [
        restoreCache.name,
      ],
      environment: {
        POETRY_CACHE_DIR: '/drone/src/.poetry-cache',
        POETRY_VIRTUALENVS_IN_PROJECT: 'false',
      },
      commands: [
        |||
          export POETRY_HOME=$DRONE_WORKSPACE/.poetry
          if [ ! -d "$POETRY_HOME" ]; then
            curl -fsS -o /tmp/get-poetry.py https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py
            python /tmp/get-poetry.py -y
          fi
        |||,
        '. .poetry/env',
        'poetry install --no-root',
      ],
    },
    common {
      name: 'lint-python',
      commands+: [
        'black . --check',
        'isort --check-only .',
        'mypy  .',
      ],
    },
    common {
      name: 'pylint',
      commands+: [
        'pylint django_apps config',
      ],
    },
    common {
      name: 'test_python',
      commands+: [
        'pytest --cov=django_apps django_apps',
      ],
    },
    rebuildCache,
  ],
};


pythonPipeline
