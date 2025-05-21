FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Create the default upload folder
# This folder will ideally be mounted as a volume in docker-compose
RUN mkdir -p uploads

# Expose the port the app runs on
EXPOSE 8050

# Set default port for Gunicorn, can be overridden by UPLOAD_SERVICE_PORT env var
ENV UPLOAD_SERVICE_PORT 8050

# Run the application using Gunicorn
CMD ["gunicorn", "-b", ":${UPLOAD_SERVICE_PORT}", "app:app"]
