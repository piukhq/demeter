FROM python:3.7
WORKDIR /app
COPY demeter /app/demeter
COPY pyproject.toml /app
COPY poetry.lock /app

RUN pip --no-cache-dir install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev

CMD ["python", "-m", "demeter.amex"]
