FROM python:3.11-slim

WORKDIR /app

RUN pip install metaapi-cloud-sdk

COPY main.py .

CMD ["python", "-u", "main.py"]
