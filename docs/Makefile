BUILDDIR = build
SOURCEDIR = .
SPHINXBUILD = sphinx-build
SPHINXOPTS = -a -n -W --keep-going

.PHONY: clean docs help

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) html
	linkchecker --check-extern --no-warnings --user-agent Mozilla/5.0 build/html/index.html

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
