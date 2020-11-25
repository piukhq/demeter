FROM binkhq/python:3.8
WORKDIR /app
COPY demeter /app/demeter
COPY Pipfile /app
COPY Pipfile.lock /app

RUN pip --no-cache-dir install pipenv && \
    pipenv install --system --deploy --ignore-pipfile

CMD ["python", "-m", "demeter.amex"]
