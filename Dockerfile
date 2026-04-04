FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y curl
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set environment variable for Flask
ENV FLASK_APP=app:create_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Run Flask dev server
CMD ["flask", "run"]