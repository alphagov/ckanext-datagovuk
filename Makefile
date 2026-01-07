.DEFAULT_GOAL := help

## DEVELOPMENT

.PHONY: build
build: ## Set up everything to run the app
	docker compose -f ./docker/docker-compose-2.10.yml build

.PHONY: run
run: ## Run the local docker stack
	docker compose -f ./docker/docker-compose-2.10.yml up

.PHONY: down
down: ## Stop the local docker stack
	docker compose -f ./docker/docker-compose-2.10.yml down

.PHONY: test
test: ## Test CKAN on docker stack 
	docker exec -w /usr/lib/ckan/venv/src/ckanext-datagovuk  -it ckan-2.10 ./bin/run-tests.sh

.PHONY: bootstrap
bootstrap: ## Download repositories for local build
	./docker/bootstrap.sh

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
