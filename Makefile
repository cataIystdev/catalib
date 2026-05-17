.DEFAULT_GOAL := help
PY ?= python3

.PHONY: help
help: ## Показать список доступных команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

.PHONY: install
install: ## Установить проект с dev-зависимостями в текущее окружение
	$(PY) -m pip install -e ".[dev]"

.PHONY: lint
lint: ## Проверить код линтером ruff
	$(PY) -m ruff check src tests

.PHONY: format
format: ## Отформатировать код через ruff
	$(PY) -m ruff format src tests

.PHONY: test
test: ## Прогнать тесты с покрытием
	$(PY) -m pytest --cov

.PHONY: build
build: ## Собрать дистрибутив пакета catalib
	$(PY) -m build
