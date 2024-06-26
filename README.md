# django_wtf

The Django Package Index.

### Project setup

Install [Docker](https://docs.docker.com/get-docker/) since we dockerize external services such as Postgres and Redis.

Clone the project:

```
git clone git@github.com:danihodovic/django_wtf.git
cd django_wtf
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

## Dumping production data for local development

Dump the data from the database into the worker pod.
```
kubectl exec -it django-wtf-worker-0 -- ./manage.py dumpdata core -o data.json.gz
```

Copy the data from the worker pod.
```
kubectl cp django-wtf-worker-0:/app/data.json.gz data.json.gz
```

Delete the Profile models which will cascade into a full delete.
```
Profile.objects.all().delete()
```

Load the data into the local database.
```
./manage.py loaddata data.json.gz
```
