FROM ghcr.io/binkhq/python:3.9-pipenv

WORKDIR /app
COPY demeter /app/demeter
COPY Pipfile /app
COPY Pipfile.lock /app

RUN pipenv install --system --deploy --ignore-pipfile

ENTRYPOINT [ "linkerd-await", "--" ]
CMD ["python", "-m", "demeter.amex"]
