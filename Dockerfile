FROM python:3.9-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt update
RUN apt install --assume-yes libpq-dev python3-dev

# install dependencies
COPY requirements.txt /app/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .
RUN python3 manage.py collectstatic
