FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y curl

# Install dependencies
COPY pyproject.toml .
RUN uv sync --no-dev

# Copy the rest of the app
COPY . .

ENV FLASK_APP=app:create_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "app:create_app()"]
