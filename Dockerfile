ARG PYTHON_VERSION

FROM lambci/lambda:build-python${PYTHON_VERSION}

COPY requirements.txt /application/requirements.txt

RUN pip install -r /application/requirements.txt --upgrade

COPY lambda_deployer /application/lambda_deployer
COPY main.py /application/main.py

ENTRYPOINT ["python", "-u", "/application/main.py"]
