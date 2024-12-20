ARG BTD_VERSION="latest"

FROM ghcr.io/stephengolub/bambu_timelapse_downloader:${BTD_VERSION}

ARG PYINSTALLER_TAG
ENV PYINSTALLER_TAG ${PYINSTALLER_TAG:-"v5"}

ARG APP_DIR="/app"
ENV APP_DIR=${APP_DIR}

# Official Python base image is needed or some applications will segfault.
# PyInstaller needs zlib-dev, gcc, libc-dev, and musl-dev
RUN apk --update --no-cache add \
    zlib-dev \
    musl-dev \
    libc-dev \
    libffi-dev \
    gcc \
    g++ \
    git \
    pwgen

ENV CFLAGS="-Wno-stringop-overflow -Wno-stringop-truncation"

# Install pycrypto so --key can be used with PyInstaller
RUN poetry install --with=build-alpine

RUN poetry run --quiet which python > /.cmd-python
RUN poetry run --quiet which pip > /.cmd-pip

# Build bootloader for alpine

RUN git clone --depth 1 --single-branch --branch ${PYINSTALLER_TAG} https://github.com/pyinstaller/pyinstaller.git /tmp/pyinstaller

WORKDIR /tmp/pyinstaller/bootloader

RUN eval $(cat /.cmd-python) ./waf configure --no-lsb all
RUN $(cat /.cmd-pip) install ..

RUN rm -Rf /tmp/pyinstaller /.cmd-*

WORKDIR /app

VOLUME /dist

ENTRYPOINT ["poetry", "run", "build"]
