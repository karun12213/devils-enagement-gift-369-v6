FROM python:3.11-slim

WORKDIR /app

# Force a clean install and verify it
RUN pip install --no-cache-dir metaapi-cloud-sdk
RUN python -c "import metaapi_sdk; print('MetaApi SDK successfully imported!')"

COPY main.py .

# Run the bot
CMD ["python", "-u", "main.py"]
