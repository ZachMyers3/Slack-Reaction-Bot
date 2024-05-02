FROM python:3.11-slim-bookworm

# System deps:
RUN pip install poetry

RUN poetry --version

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false
RUN poetry run python -m pip install --upgrade pip
RUN poetry install --no-root --no-dev

# Creating folders, and files for a project:
COPY ./src/app.py app.py
# We customize how our app is loaded with the custom entrypoint:
CMD [ "python3", "-u", "app.py"]

