.PHONY: build up down shell test run clean logs lint format

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

shell:
	docker-compose exec kotoba bash

logs:
	docker-compose logs -f

# Development commands
dev:
	docker-compose run --rm kotoba kotoba --config configs/dev.yaml

test:
	docker-compose run --rm kotoba pytest tests/ -v

run:
	docker-compose run --rm kotoba kotoba $(ARGS)

# Local installation commands
install-local:
	pip install -e .
	playwright install chromium

run-local:
	kotoba $(ARGS)

dev-local:
	kotoba --config configs/dev.yaml

# Test with lightweight setup (no LLM)
test-light:
	docker-compose -f docker-compose.test.yml build
	docker-compose -f docker-compose.test.yml up -d
	docker-compose -f docker-compose.test.yml exec kotoba-test kotoba --config configs/dev.yaml -t tests/the_internet_test.yaml --no-headless
	docker-compose -f docker-compose.test.yml down

run-light:
	docker-compose -f docker-compose.test.yml run --rm kotoba-test kotoba $(ARGS)

# Code quality
lint:
	docker-compose run --rm kotoba ruff check src/ tests/

format:
	docker-compose run --rm kotoba ruff format src/ tests/

# Clean commands
clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-cache:
	docker-compose down -v
	docker volume rm kotoba_hf_cache kotoba_pip_cache kotoba_torch_cache || true

# Model management
download-model:
	docker-compose run --rm kotoba python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('$(MODEL)'); AutoModelForCausalLM.from_pretrained('$(MODEL)')"

list-models:
	docker-compose run --rm kotoba python -c "import os; print('Cached models:'); [print(f) for f in os.listdir('/home/testuser/.cache/huggingface/hub') if f.startswith('models--')]"

# Installation
install:
	@echo "Building Docker image..."
	@make build
	@echo "Installation complete!"

# Help
help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker image"
	@echo "  make up       - Start containers in detached mode"
	@echo "  make down     - Stop containers"
	@echo "  make shell    - Enter container shell"
	@echo "  make test     - Run tests"
	@echo "  make run      - Run kotoba with arguments (ARGS='--help')"
	@echo "  make dev      - Run in development mode"
	@echo "  make lint     - Run linter"
	@echo "  make format   - Format code"
	@echo "  make clean    - Clean up temporary files"
	@echo "  make clean-cache - Clean up all Docker volumes and caches"
	@echo "  make download-model MODEL=<model_name> - Pre-download specific model"
	@echo "  make list-models - List cached models"