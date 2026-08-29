FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y \
       --no-install-recommends \
       docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY chaos.py .

CMD ["python", "chaos.py"]