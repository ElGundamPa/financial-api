.PHONY: dev install test lint clean

# Development
dev:
	uvicorn api.index:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Lint code
lint:
	python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Clean cache and temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage

# Run local server for Vercel testing
vercel-dev:
	uvicorn api.index:app --host 0.0.0.0 --port 8000

# Health check
health:
	curl http://localhost:8000/health

# Test endpoints
test-endpoints:
	curl http://localhost:8000/
	curl http://localhost:8000/sources
	curl http://localhost:8000/datos
	curl http://localhost:8000/datos/resume
