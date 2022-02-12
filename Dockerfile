FROM python:3.8-alpine

RUN apk update \
  # psycopg2 dependencies
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-dev \
  # Pillow dependencies
  && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  # CFFI dependencies
  && apk add libffi-dev py-cffi \
  # PyNaCl dependencies
  && apk add make \
  # Ability to install packages via git
  && apk add git

WORKDIR /app

RUN pip install poetry==1.1.4 #!COMMIT
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction #!COMMIT

RUN mkdir /root/.ptpython
COPY .ptpython_config.py /root/.ptpython/config.py

COPY . /app/

CMD ["gunicorn", "-b", "0.0.0.0:80", "config.wsgi", "--timeout", "90"]
