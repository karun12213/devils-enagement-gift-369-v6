FROM python:3.11-slim

WORKDIR /app

# Force a clean install and verify it with the correct module name
RUN pip install --no-cache-dir metaapi-cloud-sdk
RUN python -c "from metaapi_cloud_sdk import MetaApi; print('MetaApi SDK successfully imported!')"

COPY main.py .

# Run the bot
CMD ["python", "-u", "main.py"]
