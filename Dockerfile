# Stage 1: Build the React Frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install required OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code
COPY . .

# Copy the compiled React frontend from Stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Ensure structural directories exist to prevent FileNotFoundError
RUN mkdir -p output data

# Expose standard Cloud Run port
EXPOSE 8080

# Dynamically bind to the PORT environment variable supplied by Google Cloud Run
CMD ["sh", "-c", "uvicorn app_api:app --host 0.0.0.0 --port ${PORT:-8080}"]