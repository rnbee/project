FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev
RUN pip install --no-cache-dir --upgrade poetry==1.8.3
WORKDIR /international_delivery_project
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install
COPY ./app .
CMD ["poetry", "run", "python", "main.py"]
