ARG PYTHON_VERSION

FROM lambci/lambda:build-python${PYTHON_VERSION}

COPY pyproject.toml /application/pyproject.toml
COPY README.md /application/README.md

WORKDIR /application

# hadolint ignore=DL3033
RUN yum install -y wget \
 && yum clean all \
 && wget --output-document="${HOME}/.install-poetry.py" --quiet \
    "https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py" \
 && python "${HOME}/.install-poetry.py" --yes \
 && poetry config virtualenvs.create false \
 && poetry install --extras shell --no-root

COPY reviser /application/reviser

ENV PATH="/var/lang/pipx/venvs/poetry/bin:${PATH}"

RUN poetry config virtualenvs.create false \
 && poetry install

ENTRYPOINT ["reviser-shell"]
