FROM python:3.11-slim

WORKDIR /app

# Install standard compiler tools compatible with Debian Trixie minimal image
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["streamlit", "run", "app_dashboard.py", "--server.port=8080", "--server.address=0.0.0.0"]
