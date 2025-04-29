DEVPKGS  = $(shell cat devpkgs)
ENVNAME  = mpas_app
ENVPATH  = $(shell ls $(CONDA_PREFIX)/envs/$(ENVNAME) 2>/dev/null)
TARGETS  = devenv env format lint rmenv test typecheck unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

devenv: env
	conda install -y -n $(ENVNAME) $(DEVPKGS)

env: rmenv
	conda env create

format:
	@./format

lint:
	ruff check ush

regtest:
	pytest --cov -k "regtest" -n 4 tests

rmenv:
	$(if $(ENVPATH),conda env remove -y -n $(ENVNAME))

test: lint typecheck unittest

typecheck:
	mypy --install-types --non-interactive ush

unittest:
	pytest --cov -k "not regtest" -n 4 tests
