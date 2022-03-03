local pythonStepCommon = {
  depends_on: ['install-python-deps'],
  volumes: [
    { name: 'cache', path: '/tmp/cache' },
  ],
  commands: [
    '. .poetry/cache/virtualenvs/*/bin/activate',
  ],
};

local installDepsStep = pythonStepCommon {
  name: 'install-python-deps',
  depends_on: ['restore-cache'],
  commands: [
    |||
      export POETRY_HOME=$DRONE_WORKSPACE/.poetry
      export POETRY_CACHE_DIR=$POETRY_HOME/cache
      if [ ! -d "$POETRY_HOME" ]; then
        curl -fsS -o /tmp/install-poetry.py https://install.python-poetry.org
        python /tmp/install-poetry.py -y
      fi
    |||,
    '$POETRY_HOME/bin/poetry install --no-root',
  ],
};

local formatStep = pythonStepCommon {
  name: 'format',
  commands+: [
    'black . --check',
    'isort --check-only .',
  ],
};

local mypyStep = pythonStepCommon {
  name: 'typecheck',
  commands+: [
    'mypy .',
  ],
};


local pylintStep = pythonStepCommon {
  name: 'lint',
  commands+: [
    "pylint $(git ls-files -- '*.py' ':!:**/migrations/*.py')",
  ],
};

local testStep = pythonStepCommon {
  name: 'test',
  commands+: ['pytest --ignore=.poetry --cov'],
};


local pipelineCommon(image) = {
  kind: 'pipeline',
  type: 'docker',
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
        path: '/tmp/cache',
      },
    },
    {
      name: 'poetry',
      temp: {},
    },
    {
      name: 'poetry-cache',
      temp: {},
    },
  ],
  steps: [
    installDepsStep { image: image },
    formatStep { image: image },
    mypyStep { image: image },
    pylintStep { image: image },
    testStep { image: image },
  ],
};

{
  pythonPipeline: {
    new(pipeline, image): pipelineCommon(image) + pipeline,
  },
  dockerPipeline: {
    kind: 'pipeline',
    type: 'docker',
  },
}
