.PHONY: install dev lint fix format run clean

install: ## Install dependencies
	uv sync --no-dev

dev: ## Install all dependencies (including dev)
	uv sync

lint: ## Run linter
	uv run ruff check src/ main.py

fix: ## Auto-fix lint issues
	uv run ruff check --fix src/ main.py

format: ## Format code
	uv run ruff format src/ main.py

run: ## Run the full pipeline
	uv run python main.py run

clean: ## Remove caches
	rm -rf __pycache__ src/__pycache__ .ruff_cache