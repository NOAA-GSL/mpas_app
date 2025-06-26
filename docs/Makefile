BUILDDIR = build
SOURCEDIR = .
SPHINXBUILD = sphinx-build
SPHINXOPTS = --fail-on-warning --nitpicky --write-all

.PHONY: clean docs help

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) html
	linkchecker --check-extern --no-warnings build/html/index.html

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
