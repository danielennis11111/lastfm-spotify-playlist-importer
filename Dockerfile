FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

ENV PORT=8080
ENV ENVIRONMENT=production

# Set worker timeout to 120 seconds
CMD exec gunicorn --bind :$PORT --timeout 120 --workers 1 app:app 