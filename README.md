# django_apps

### Project setup

Install [Docker](https://docs.docker.com/get-docker/) since we dockerize external services such as Postgres and Redis.

Clone the project:

```
git clone git@github.com:danihodovic/django_apps.git
cd django_apps
```

Add the direnv file
```
echo 'dotenv' > .envrc
direnv allow
```

Install the python version
```
PYTHON_CONFIGURE_OPTS=--enable-shared pyenv install $(cat .python-version)
pyenv local $(cat .python-version)
```

Configure the virtual environment
```
python -m venv .venv && cd .
```

Install poetry and the dependencies
```
pip install poetry && poetry install
```

Start the docker-compose services
```
docker-compose up -d
```

Run the migrations
```
./manage.py migrate
```

Start the Django server
```
./manage.py runserver_plus
```

Enter the Django shell
```
./manage.py shell_plus
```
