local drone = import 'vendor/github.com/danihodovic/drone-jsonnet/python.libsonnet';

local cacheStepCommon = {
  image: 'meltwater/drone-cache',
  environment: {
    AWS_ACCESS_KEY_ID: {
      from_secret: 'AWS_ACCESS_KEY_ID',
    },
    AWS_SECRET_ACCESS_KEY: {
      from_secret: 'AWS_SECRET_ACCESS_KEY',
    },
  },
  settings: {
    cache_key: '{{ .Repo.Name }}_{{ checksum "poetry.lock" }}',
    region: 'eu-central-1',
    bucket: 'depode-ci-cache',
    mount: ['.poetry'],
  },
  volumes: [{ name: 'cache', path: '/tmp/cache' }],
};

local rebuildCacheStep = cacheStepCommon {
  name: 'rebuild-cache',
  depends_on: [
    'install-python-deps',
  ],
  settings+: {
    rebuild: true,
  },
};

local restoreCacheStep = cacheStepCommon {
  name: 'restore-cache',
  settings+: {
    restore: true,
  },
};


local pythonPipelineWithoutCache = drone.pythonPipeline.new({
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
  environment: {
    POETRY_CACHE_DIR: '/drone/src/.poetry-cache',
    POETRY_VIRTUALENVS_IN_PROJECT: 'false',
    DJANGO_SETTINGS_MODULE: 'config.settings.test',
    DATABASE_URL: 'postgres://postgres:postgres@postgres:5432/django-apps',
    REDIS_URL: 'redis://redis:6379/',
    CELERY_BROKER_URL: 'redis://redis:6379/0',
  },
}, 'python:3.8');

local pythonPipeline = pythonPipelineWithoutCache {
  steps: [restoreCacheStep] + pythonPipelineWithoutCache.steps + [rebuildCacheStep],
};

local pushImagePipeline = {
  name: 'push-image',
  depends_on: ['python'],
  kind: 'pipeline',
  type: 'docker',
  trigger: {
    event: [
      'push',
    ],
  },
  steps: [
    {
      name: 'Push Docker image',
      image: 'plugins/docker',
      settings: {
        username: 'depode',
        password: { from_secret: 'docker_registry_password' },
        repo: 'registry.depode.com/django-apps',
        registry: 'registry.depode.com',
        cache_from: 'registry.depode.com/django-apps:cache',
        tags: ['cache', '${DRONE_COMMIT_SHA:0:7}'],
      },
    },
  ],
};

local promote = drone.dockerPipeline {
  name: 'trigger-production',
  depends_on: ['python'],
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

local deploy = drone.dockerPipeline {
  depends_on: ['python', 'push-image'],
  trigger: {
    event: ['promote'],
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
  pushImagePipeline,
  deploy,
]
