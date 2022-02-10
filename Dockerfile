FROM python:3.7-alpine

RUN apk update \
  # psycopg2 dependencies
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-dev \
  # Pillow dependencies
  && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  # CFFI dependencies
  && apk add libffi-dev py-cffi \
  # Ability to install packages via git
  && apk add git

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN mkdir /root/.ptpython
COPY .ptpython_config.py /root/.ptpython/config.py

ENV PYTHONUNBUFFERED 1
ENV PYTHONBREAKPOINT pudb.set_trace

WORKDIR /app

COPY . /app/
