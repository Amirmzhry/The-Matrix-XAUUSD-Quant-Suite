.PHONY: install dev-backend dev-frontend deploy test clean

install:
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev-backend:
	@echo "Starting FastAPI backend server..."
	python app_api.py

dev-frontend:
	@echo "Starting React frontend server..."
	cd frontend && npm run dev

deploy:
	@echo "Deploying to Google Cloud Run..."
	gcloud run deploy the-matrix-quant-suite --source . --region us-central1 --allow-unauthenticated

test:
	@echo "Running tests..."
	pytest tests/

clean:
	@echo "Cleaning up __pycache__ and build artifacts..."
	if exist "frontend\dist" rmdir /s /q "frontend\dist"
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
