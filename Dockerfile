ARG BASE_IMAGE=ilyanekhay/poetry:poetry1.7.1-py3.11

FROM ${BASE_IMAGE} as builder

WORKDIR /opt/app

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

FROM ${BASE_IMAGE}-slim as runtime

WORKDIR /opt/app

COPY --from=builder /opt/virtualenvs /opt/virtualenvs

COPY pyproject.toml poetry.lock ./
COPY src ./src

RUN ls -la

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install

EXPOSE 80
ENTRYPOINT ["poetry", "run", "uvicorn", "doggo.app:app", "--host", "0.0.0.0", "--port", "80"]
