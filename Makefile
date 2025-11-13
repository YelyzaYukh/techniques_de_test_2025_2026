# ==== Variables ====
PYTHON := python3
TEST_DIR := TP/tests/unitaires
SRC_DIR := TP
DOC_DIR := docs

# ==== Default target ====
.PHONY: all
all: test

# ==== Testing ====
.PHONY: test unit_test perf_test

test:
	@echo "Running all tests..."
	pytest $(TEST_DIR)

unit_test:
	@echo "Running unit tests (excluding performance tests)..."
	pytest $(TEST_DIR) -k "not perf"

perf_test:
	@echo "Running performance tests only..."
	pytest $(TEST_DIR) -k "perf"

# ==== Coverage ====
.PHONY: coverage
coverage:
	@echo "Generating coverage report..."
	coverage run -m pytest $(TEST_DIR)
	coverage report -m
	coverage html
	@echo "HTML report generated in 'htmlcov/index.html'"

# ==== Lint ====
.PHONY: lint
lint:
	@echo "Running Ruff linter..."
	ruff check $(SRC_DIR) $(TEST_DIR)

# ==== Documentation ====
.PHONY: doc
doc:
	@echo "Generating HTML documentation with pdoc3..."
	pdoc3 --html $(SRC_DIR) --output-dir $(DOC_DIR) --force
	@echo "Documentation generated in '$(DOC_DIR)/'"

# ==== Cleanup ====
.PHONY: clean
clean:
	@echo "Cleaning up generated files..."
	rm -rf __pycache__ .pytest_cache htmlcov $(DOC_DIR)
	find . -name "*.pyc" -delete
