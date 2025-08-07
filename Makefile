REGTEST = pytest --basetemp=$(PWD)/.pytest --verbose tests/regtest.py
REMOTES = hera|jet|ursa
TARGETS = devenv docs env format lint regtest regtest-data regtest-regen systest test typecheck unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

devenv:
	MPAS_APP_DEVENV=1 bin/build --conda-only

docs:
	$(MAKE) -C docs docs

env:
	bin/build --conda-only

format:
	@./bin/format

lint:
	ruff check .

regtest: regtest-data
	@test -z "$(remote)" && echo 'Set remote=$(REMOTES)' && exit 1 || true
	dvc pull --remote $(remote)
	$(REGTEST)

regtest-regen:
	$(REGTEST) --regen-all
	@echo "*** To update baseline, run: dvc push --remote $(REMOTES)"

systest:
	pytest -k "systest" -n 5 tests/*

test: lint typecheck unittest

typecheck:
	mypy --install-types --non-interactive .

unittest:
	pytest --cov -k "not regtest and not systest" -n 8 tests
