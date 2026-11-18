#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = sonora-health-climate-eda
PYTHON_VERSION = 3.13
PYTHON_INTERPRETER ?= $(firstword $(wildcard $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV)/bin/python) venv/bin/python .venv/bin/python) python)

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python dependencies
.PHONY: requirements
requirements:
	uv pip install --python $(PYTHON_INTERPRETER) -r requirements.txt
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete


## Lint using ruff (use `make format` to do formatting)
.PHONY: lint
lint:
	uvx ruff format --check
	uvx ruff check

## Format source code with ruff
.PHONY: format
format:
	uvx ruff check --fix
	uvx ruff format







#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


## Make dataset
.PHONY: data
data:
	$(PYTHON_INTERPRETER) -m sonora_health_climate_eda.dataset data-ingestion-pipeline

## Process air quality (hourly -> daily -> weekly -> monthly)
.PHONY: aire
aire:
	$(PYTHON_INTERPRETER) -m sonora_health_climate_eda.aire horario
	$(PYTHON_INTERPRETER) -m sonora_health_climate_eda.aire diario
	$(PYTHON_INTERPRETER) -m sonora_health_climate_eda.aire semanal
	$(PYTHON_INTERPRETER) -m sonora_health_climate_eda.aire mensual


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
