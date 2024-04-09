FROM python:3.11.6-alpine3.18
ENV POETRY_VERSION=1.8.2
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

WORKDIR /app

# geos-dev is required for shapely, proj for pyproj
RUN apk add --no-cache g++ geos-dev proj-util proj-dev

COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --without dev

COPY alembic.ini prestart.sh /app/
COPY migrations /app/migrations
COPY app /app/app

ENTRYPOINT sh prestart.sh
