ACTIVATE = . conda/etc/profile.d/conda.sh && conda activate
DEVPKGS  = $(shell cat devpkgs)
ENVNAME  = mpas_app
ENVPATH  = $(shell ls $(CONDA_PREFIX)/envs/$(ENVNAME) 2>/dev/null)
TARGETS  = conda devenv docs env format lint rmenv test typecheck unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

conda:
	./build.sh --conda-only

devenv: env
	$(ACTIVATE) && mamba install -y -n $(ENVNAME) $(DEVPKGS)

docs:
	$(MAKE) -C docs docs

env: conda rmenv
	$(ACTIVATE) && mamba env create -y -f environment.yml

format:
	@./format

lint:
	ruff check .

regtest:
	pytest --basetemp=$(PWD)/.pytest -k "regtest" tests/*

rmenv:
	$(if $(ENVPATH),conda env remove -y -n $(ENVNAME))

systest:
	pytest -k "systest" -n 5 tests/*

test: lint typecheck unittest

typecheck:
	mypy --install-types --non-interactive .

unittest:
	pytest --cov -k "not regtest and not systest" -n 8 tests
