ARG PYTHON_VERSION

FROM amazon/aws-lambda-python:${PYTHON_VERSION}

COPY pyproject.toml /application/pyproject.toml
COPY README.md /application/README.md

WORKDIR /application

ENV PATH="/root/.local/bin:/var/lang/pipx/venvs/poetry/bin:${PATH}"

# hadolint ignore=DL3033
RUN pip --no-cache-dir install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --extras shell --no-root

COPY reviser /application/reviser

RUN poetry config virtualenvs.create false \
 && poetry install --extras shell

ENTRYPOINT ["reviser-shell"]
