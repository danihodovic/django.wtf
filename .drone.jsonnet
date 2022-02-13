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
        'pylint django_apps',
      ],
    },
    common {
      name: 'test_python',
      commands+: [
        'pytest --cov=django_apps django_apps',
      ],
    },
    {
      name: 'Push Docker image',
      image: 'plugins/docker',
      depends_on: ['test_python'],
      settings: {
        username: 'depode',
        password: { from_secret: 'docker_registry_password' },
        repo: 'registry.depode.com/django-apps',
        registry: 'registry.depode.com',
        cache_from: 'registry.depode.com/django-apps:cache',
        tags: ['cache', '${DRONE_COMMIT_SHA:0:7}'],
      },
    },
    rebuildCache,
  ],
};

local promote = pipelineCommon {
  name: 'trigger-production',
  depends_on: [
    'python',
  ],
  trigger: {
    branch: [
      'master',
    ],
    event: [
      'push',
    ],
  },
  steps: [
    {
      name: 'promote-production',
      image: 'danihodovic/drone-promote',
      settings: {
        drone_token: {
          from_secret: 'drone_token',
        },
        target: 'production',
      },
    },
  ],
};

local deploy = pipelineCommon {
  depends_on: [
    'python',
  ],
  trigger: {
    event: [
      'promote',
    ],
    target: 'production',
  },
  steps: [
    {
      name: 'deploy',
      image: 'honeylogic/tanka',
      environment: {
        AGE_PRIVATE_KEY: {
          from_secret: 'AGE_PRIVATE_KEY',
        },
      },
      commands: [
        'export GIT_COMMIT=$(git rev-parse --short HEAD)',
        'git clone https://github.com/danihodovic/depode-infra.git',
        'cd depode-infra',
        'echo $AGE_PRIVATE_KEY > ~/.config/sops/age/keys.txt',
        'task apply-prod -- tanka/environments/default/django_apps.jsonnet $GIT_COMMIT',
      ],
    },
  ],
};


[
  pythonPipeline,
  promote,
  deploy,
]
