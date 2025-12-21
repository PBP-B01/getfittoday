# --- Stage 1: Build Stage ---
# Use an official Python runtime as a parent image on Alpine for smaller size
FROM python:3.11-alpine AS builder

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies needed for building Python packages (like psycopg2)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev 

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime Stage ---
FROM python:3.11-alpine AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PRODUCTION True

# Install only necessary runtime system dependencies (PostgreSQL client)
RUN apk add --no-cache libpq

# Set the working directory
WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the rest of the application code into the container
COPY . .

RUN python manage.py migrate --noinput

# Run collectstatic to gather static files for WhiteNoise
# Use --noinput to automatically confirm
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on (Gunicorn default is 8000)
EXPOSE 8000

# Define the command to run the application using Gunicorn
# Binds to all network interfaces on port 8000
# Ensure 'getfittoday.wsgi:application' matches your project structure
CMD ["gunicorn", "--bind", "0.0.0.0:80", "getfittoday.wsgi:application"]