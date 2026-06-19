FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install the package DIRECTLY, bypassing requirements.txt
RUN pip install metaapi-cloud-sdk

# Copy the bot script
COPY main.py .

# Run the bot
CMD ["python", "main.py"]
