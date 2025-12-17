# ==== Variables ====
PYTHON := python3
TEST_DIR := TP/tests
SRC_DIR := TP
DOC_DIR := docs

# Put source dir on PYTHONPATH for test runs (use absolute path to avoid import issues)
ENV_PY := PYTHONPATH=$(abspath $(SRC_DIR))

# ==== Default target ====
.PHONY: all
all: test

# ==== Prepare virtualenv / deps ====
.PHONY: deps
deps:
	@echo "Creating venv and installing minimal dev dependencies..."
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	# install runtime + dev requirements (from project files)
	. .venv/bin/activate && pip install -r requirements.txt
	. .venv/bin/activate && pip install -r dev_requirements.txt

# ==== Testing ====
.PHONY: test unit_test perf_test

test:
	@echo "Running all tests..."
	$(ENV_PY) pytest $(TEST_DIR)

unit_test:
	@echo "Running unit tests (excluding performance tests)..."
	$(ENV_PY) pytest $(TEST_DIR) -k "not perf"

perf_test:
	@echo "Running performance tests only..."
	$(ENV_PY) pytest $(TEST_DIR) -k "perf"

# ==== Coverage ====
.PHONY: coverage
coverage:
	@echo "Generating coverage report..."
	$(ENV_PY) coverage run -m pytest $(TEST_DIR)
	coverage report -m
	coverage html
	@echo "HTML report generated in 'htmlcov/index.html'"

# ==== Lint ====
.PHONY: lint
lint:
	@echo "Running Ruff linter..."
	$(ENV_PY) ruff check $(SRC_DIR) $(TEST_DIR)

# ==== Documentation ====
.PHONY: doc
doc:
	@echo "Generating HTML documentation with pdoc3..."
	$(ENV_PY) pdoc3 --html $(SRC_DIR) --output-dir $(DOC_DIR) --force
	@echo "Documentation generated in '$(DOC_DIR)/'"

# ==== Cleanup ====
.PHONY: clean
clean:
	@echo "Cleaning up generated files..."
	rm -rf __pycache__ .pytest_cache htmlcov $(DOC_DIR) .venv
	find . -name "*.pyc" -delete
