FROM python:3.13-alpine

# Install minimal dependencies
RUN apt-get update && apt-get install -y

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install uvicorn-worker gunicorn

COPY app ./

COPY gunicorn.conf.py ./

COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]