ARG PYTHON_VERSION

FROM lambci/lambda:build-python${PYTHON_VERSION}

COPY pyproject.toml /application/pyproject.toml
COPY README.md /application/README.md

RUN pip install poetry \
 && cd /application \
 && poetry config virtualenvs.create false \
 && poetry install --extras shell --no-root

COPY reviser /application/reviser

RUN cd /application \
 && poetry config virtualenvs.create false \
 && poetry install

ENTRYPOINT ["reviser-shell"]
