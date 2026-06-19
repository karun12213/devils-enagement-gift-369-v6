FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies globally in the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script
COPY main.py .

# Run the bot
CMD ["python", "main.py"]
