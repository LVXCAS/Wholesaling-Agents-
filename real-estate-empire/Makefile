# Real Estate Empire Makefile

.PHONY: help build start stop clean test deploy logs

# Default environment
ENV ?= development

help: ## Show this help message
	@echo "Real Estate Empire - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all services
	docker-compose build

start: ## Start all services
	docker-compose -f docker-compose.yml up -d
	@echo "Services starting... API Gateway will be available at http://localhost:8000"

stop: ## Stop all services
	docker-compose down

clean: ## Clean up containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

test: ## Run tests for all services
	@echo "Running tests for all services..."
	@for service in api-gateway auth-service property-service lead-service outreach-service transaction-service portfolio-service reporting-service ml-service; do \
		echo "Testing $$service..."; \
		cd services/$$service && python -m pytest tests/ || exit 1; \
		cd ../..; \
	done

test-service: ## Run tests for specific service (usage: make test-service SERVICE=api-gateway)
	@if [ -z "$(SERVICE)" ]; then echo "Please specify SERVICE (e.g., make test-service SERVICE=api-gateway)"; exit 1; fi
	cd services/$(SERVICE) && python -m pytest tests/

deploy: ## Deploy to specified environment (usage: make deploy ENV=staging)
	@echo "Deploying to $(ENV) environment..."
	bash scripts/deploy.sh $(ENV)

logs: ## Show logs for all services
	docker-compose logs -f

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=api-gateway)
	@if [ -z "$(SERVICE)" ]; then echo "Please specify SERVICE (e.g., make logs-service SERVICE=api-gateway)"; exit 1; fi
	docker-compose logs -f $(SERVICE)

db-init: ## Initialize databases
	python scripts/init_db.py

db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	@for service in auth property lead outreach transaction portfolio reporting; do \
		echo "Migrating $$service database..."; \
		docker-compose exec postgres psql -U postgres -c "CREATE DATABASE IF NOT EXISTS $${service}_db;"; \
	done

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/services/status | python -m json.tool

install: ## Install development dependencies
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ]; then \
			echo "Installing dependencies for $$service"; \
			cd "$$service" && pip install -r requirements.txt && cd ../..; \
		fi; \
	done

dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	cp environments/development.env .env
	make build
	make start
	sleep 30
	make db-init
	@echo "Development environment ready!"

prod-deploy: ## Deploy to production
	make deploy ENV=production

staging-deploy: ## Deploy to staging
	make deploy ENV=staging