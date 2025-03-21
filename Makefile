# Shell Metamorphic Differential Testing Framework Makefile

# Python settings
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Project directories
SRC_DIR := src
RESULTS_DIR := results
CONFIG_DIR := configs
CORPUS_DIR := corpus
MUTATORS_DIR := $(SRC_DIR)/mutation_chain/mutators
REPORT_DIR := $(RESULTS_DIR)/reports
TRANRES_DIR := $(RESULTS_DIR)/posix_code
BACKUP_DIR := $(RESULTS_DIR)/backup

# Configuration
CONFIG_FILE := $(CONFIG_DIR)/conf.json


# Timestamps for backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

# Colors for output, using ANSI escape codes
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help init venv test mutators clean clean-reports clean-mutators clean-venv

# Default target
help:
	@echo "$(GREEN)Shell Metamorphic Differential Testing Framework$(NC)"
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make init          - Initialize the project (create venv, install dependencies)"
	@echo "  make venv          - Create Python virtual environment"
	@echo "  make mutators      - Generate mutators (backs up existing ones)"
	@echo "  make test          - Run differential tests"
	@echo "  make clean         - Clean up all generated files"
	@echo "  make clean-reports - Clean up test reports only"
	@echo "  make clean-mutators- Clean up mutators only"
	@echo "  make clean-venv    - Remove virtual environment"
	@echo "  make help          - Show this help message"

# Initialize the project
init: venv
	@echo "$(GREEN)Initializing project...$(NC)"
    @bash scripts/init.sh

# Create virtual environment
venv:
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)Virtual environment created.$(NC)"; \
	else \
		echo "$(YELLOW)Virtual environment already exists.$(NC)"; \
	fi

# Generate mutators
mutators: init
	@echo "$(GREEN)Generating mutators...$(NC)"
	@if [ -d "$(MUTATORS_DIR)" ] && [ "$$(ls -A $(MUTATORS_DIR) 2>/dev/null)" ]; then \
		echo "$(YELLOW)Backing up existing mutators to $(BACKUP_DIR)/mutators_$(TIMESTAMP)$(NC)"; \
		mkdir -p $(BACKUP_DIR)/mutators_$(TIMESTAMP); \
		cp -R $(MUTATORS_DIR)/* $(BACKUP_DIR)/mutators_$(TIMESTAMP)/; \
	fi
	@echo "$(GREEN)Running mutator generation...$(NC)"
	$(PYTHON_VENV) main.py --mode prepare --config $(CONFIG_FILE)
	@echo "$(GREEN)Mutators generated successfully!$(NC)"

# Run tests
test: 
	@echo "$(GREEN)Running differential tests...$(NC)"
	@if [ ! -d "$(MUTATORS_DIR)" ] || [ -z "$$(ls -A $(MUTATORS_DIR) 2>/dev/null)" ]; then \
		echo "$(RED)Error: No mutators found in $(MUTATORS_DIR). Run 'make mutators' first.$(NC)"; \
		exit 1; \
	fi
	python main.py --mode testing
	@echo "$(GREEN)Tests completed! See $(REPORT_DIR) for results.$(NC)"
	@echo "$(GREEN)Generating the coverage report...$(NC)"
	@bash scripts/coverage.sh
	@echo "$(GREEN)Coverage report generated!$(NC)"

# Clean up generated files
clean: clean-reports clean-transformed clean-mutators clean-venv

# Clean up test reports
clean-reports:
	@echo "$(GREEN)Cleaning up test reports...$(NC)"
	@rm $(REPORT_DIR)/{*.txt,*.json}
	@echo "$(GREEN)Test reports cleaned.$(NC)"

# Clean up transformed results
clean-transformed:
	@echo "$(GREEN)Cleaning up transformed results...$(NC)"
	@rm $(TRANRES_DIR)/*.sh
	@echo "$(GREEN)Transformed results cleaned.$(NC)"

# Clean up mutators
clean-mutators:
	@echo "$(YELLOW)Are you sure you want to delete all mutators? (y/n)$(NC)"
	@read confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(GREEN)Cleaning up mutators...$(NC)"; \
		if [ -d "$(MUTATORS_DIR)" ] && [ "$$(ls -A $(MUTATORS_DIR) 2>/dev/null)" ]; then \
			echo "$(YELLOW)Backing up existing mutators to $(BACKUP_DIR)/mutators_$(TIMESTAMP) before deletion$(NC)"; \
			mkdir -p $(BACKUP_DIR)/mutators_$(TIMESTAMP); \
			cp -R $(MUTATORS_DIR)/* $(BACKUP_DIR)/mutators_$(TIMESTAMP)/; \
		fi; \
		rm -rf $(MUTATORS_DIR)/*; \
		mkdir -p $(MUTATORS_DIR); \
		echo "$(GREEN)Mutators cleaned.$(NC)"; \
	else \
		echo "$(YELLOW)Mutator deletion cancelled.$(NC)"; \
	fi

# Clean up virtual environment
clean-venv:
	@echo "$(YELLOW)Are you sure you want to delete the virtual environment? (y/n)$(NC)"
	@read confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(GREEN)Removing virtual environment...$(NC)"; \
		rm -rf $(VENV); \
		echo "$(GREEN)Virtual environment removed.$(NC)"; \
	else \
		echo "$(YELLOW)Virtual environment deletion cancelled.$(NC)"; \
	fi


