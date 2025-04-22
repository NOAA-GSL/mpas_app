ENVNAME = mpas_app
TARGETS = devenv env format lint test typecheck unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

devenv: env
	conda update -f dev.yml

env:
	conda env create

format:
	@./format

lint:
	ruff check .

rmenv:
	conda env remove -y -n $(ENVNAME)

test: lint typecheck unittest

typecheck:
	mypy --install-types --non-interactive .

unittest:
	pytest --cov=foo -n 4 .
