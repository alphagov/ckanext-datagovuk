.DEFAULT_GOAL := help

## LINTING

.PHONY: lint
lint: ## Run ruff linter
	ruff check .

.PHONY: format
format: ## Run ruff formatter
	ruff format .

.PHONY: fix
fix: ## Apply safe ruff fixes (imports, whitespace) then format
	ruff check --fix .
	ruff format .

## DEVELOPMENT

.PHONY: build
build: ## Set up everything to run the app
	docker compose -f ./docker/compose.yml build

.PHONY: run
run: ## Run the local docker stack
	docker compose -f ./docker/compose.yml up

.PHONY: down
down: ## Stop the local docker stack
	docker compose -f ./docker/compose.yml down

.PHONY: test
test: ## Test CKAN on docker stack 
	docker exec -w /usr/lib/ckan/venv/src/ckanext-datagovuk -it ckan ./bin/run-tests.sh

.PHONY: bootstrap
bootstrap: ## Download repositories for local build
	./docker/bootstrap.sh

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
