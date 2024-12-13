FROM python:3.11-slim
ENV POETRY_VIRTUALENVS_CREATE=false \
    UVICORN_RELOAD=false
WORKDIR /code
RUN pip install poetry
COPY pyproject.toml poetry.lock /code/
RUN poetry install --without dev --no-root
COPY crop_health_api/ /code/crop_health_api/

RUN groupadd -r fastapi && useradd -r -g fastapi fastapi
USER fastapi

CMD ["python", "-m", "crop_health_api"]
