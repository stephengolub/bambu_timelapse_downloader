FROM python:3.11-alpine

RUN apk update && \
    apk add libpq \
      poetry \
      musl-dev \
      build-base \
      gcc \
      gfortran \
      openblas-dev \
      ffmpeg

WORKDIR /app

COPY src ./src
COPY poetry.lock ./poetry.lock
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md

RUN poetry install

ENTRYPOINT ["poetry", "run", "bambu-ftp-download", "--console-only-logging"]
