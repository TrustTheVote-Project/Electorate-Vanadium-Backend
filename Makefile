# Makefile.
#
# This is intended for convenience.
# All commands should be usable even without make.

# --- Variables

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

PROJECT := vanadium

PIP_REQ_MAIN := requirements.txt
PIP_REQ_DEV  := requirements-dev.txt

DOCKER_TAG  := $(PROJECT)
DOCKER_APP  := $(PROJECT)-app
DOCKER_HOST := localhost
DOCKER_PORT := 8080

SERVER_APP_PATH := $(ROOT)
SERVER_APP_NAME := $(PROJECT).app.main:application
SERVER_HOST := 127.0.0.1
SERVER_PORT := 8080

SERVER_MAIN_FLAGS = --host $(SERVER_HOST) --port $(SERVER_PORT) $(SERVER_APP_NAME)
SERVER_TEST_FLAGS = --reload $(SERVER_MAIN_FLAGS)

COVERAGE_CONF := $(ROOT)/.coveragerc
COVERAGE_DATA := $(shell grep -E "datafile =" $(COVERAGE_CONF) | cut -d ' ' -f 3)

# --- Rules

help:
	@echo "Make targets:"
	@echo ""
	@echo "Project builds:"
	@echo ""
	@echo "  Notes:"
	@echo "  - These commands need an active virtualenv and use Poetry."
	@echo "    There are Pip equivalents but they are not make targets."
	@echo ""
	@echo "  install     - Install non-dev dependencies and main package"
	@echo "  develop     - Install all dependencies and main package"
	@echo "  depends     - Install all dependencies without the main package"
	@echo ""
	@echo "  build       - Build all distributable Python packages."
	@echo "  build-sdist - Build project as source tarball."
	@echo "  build-wheel - Build project as wheel."
	@echo ""
	@echo "  clean       - Remove all built Python packages."
	@echo "  clean-sdist - Remove built tarballs."
	@echo "  clean-wheel - Remove built wheels."
	@echo ""
	@echo "Pip requirements:"
	@echo ""
	@echo "  pip-requirements      - Export Pip requirements files with hashes."
	@echo "  pip-requirements-base - Export Pip requirements files without hashes."
	@echo ""
	@echo "Docker image:"
	@echo ""
	@echo "  build-docker-image - Build Docker image from Dockerfile"
	@echo "  run-docker-image   - Run Docker container"
	@echo ""
	@echo "PyTest: common commands"
	@echo ""
	@echo "  test-all           - Run all test cases"
	@echo "  test-one           - Run until first failing case"
	@echo "  test-debug         - Run debugger if any cases fail"
	@echo ""
	@echo "Coverage:"
	@echo ""
	@echo "  cover-test         - Run coverage over pytest"
	@echo "  cover-report       - Generate text report of coverage"
	@echo "                       Skips files with complete coverage"
	@echo "  cover-report-full  - Generate full text report of coverage"
	@echo "  cover-html         - Generate HTML report of coverage"
	@echo "                       Skips files with complete coverage"
	@echo "  cover-html-full    - Generate full HTML report of coverage"
	@echo "  cover-clean        - Clear out existing coverage data"
	@echo "  cover-redo         - Clear out existing data and run tests again"
	@echo ""
	@echo "Uvicorn server"
	@echo ""
	@echo "  serve              - Run uvicorn server	"
	@echo ""


# Project builds

install:
	poetry install --no-dev

develop:
	poetry install

depends:
	poetry install --no-root

build: build-sdist build-wheel

clean: clean-sdist clean-wheel

build-sdist:
	poetry build -f sdist

clean-sdist:
	rm -f dist/$(PROJECT)*.tar.gz
	rmdir --ignore-fail-on-non-empty dist

build-wheel:
	poetry build -f wheel

clean-wheel:
	rm -f dist/$(PROJECT)*.whl
	rmdir --ignore-fail-on-non-empty dist


# Pip requirements

pip-requirements:
	poetry export -f requirements.txt > $(PIP_REQ_MAIN)
	poetry export --dev -f requirements.txt > $(PIP_REQ_DEV)

pip-requirements-base:
	poetry export --without-hashes -f requirements.txt > $(PIP_REQ_MAIN)
	poetry export --without-hashes --dev -f requirements.txt > $(PIP_REQ_DEV)


# Docker

build-docker-image:
	docker build -t "$(DOCKER_TAG)" .

run-docker-image: build-docker-image
	docker run -it --rm --name "$(DOCKER_APP)" -p "$(DOCKER_PORT):$(DOCKER_PORT)" "$(DOCKER_TAG)"

# PyTest

test-all:
	pytest

test-one:
	pytest -x

test-debug:
	pytest -x --pdb

# PyTest + Coverage

cover-test:
	coverage run -m pytest

cover-report: $(COVERAGE_DATA)
	coverage report --skip-covered --skip-empty

cover-report-full: $(COVERAGE_DATA)
	coverage report

cover-html: $(COVERAGE_DATA)
	coverage html --skip-covered --skip-empty

cover-html-full: $(COVERAGE_DATA)
	coverage html

cover-clean:
	coverage erase

cover-redo: cover-clean cover-test

# Uvicorn

serve:
	uvicorn $(SERVER_MAIN_FLAGS)

serve-test:
	uvicorn $(SERVER_TEST_FLAGS)
