#################################################
# Edit the following to match your sources lists
#################################################

# Add iso code for any locales you want to support here (space separated)
LOCALES = da

# If locales are enabled, set the name of the lrelease binary on your system.
# Depending on your system you may have to provide the full path to the
# lrelease binary.
LRELEASE = lrelease

# translation
SOURCES = \
	__init__.py \
	cartogram.py \
	cartogram_dialog.py

PLUGINNAME = cartogram

PY_FILES = \
	cartogram.py \
	cartogram_dialog.py \
	cartogram_feature.py \
	cartogram_worker.py \
	__init__.py

UI_FILES = cartogram_dialog.ui

EXTRAS = metadata.txt
ASSETS = icon.png
DEMO = demo.dbf demo.prj demo.qpj demo.shp demo.shx

COMPILED_RESOURCE_FILES = cartogram_dialog.py resources_rc.py

PEP8EXCLUDE=pydev,resources_rc.py,conf.py,third_party,ui

#################################################
# Normally you would not need to edit below here
#################################################

RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed \
	's@</file>@@g;s/.*>//g' | tr '\n' ' ')

QGISDIR=.qgis2

default: compile

compile: $(COMPILED_RESOURCE_FILES)

%_rc.py: %.qrc $(RESOURCES_SRC)
	pyrcc4 -o $*_rc.py $<

%.py: %.ui
	pyuic4 -w -o $*.py $<

%.qm: %.ts
	$(LRELEASE) $<

deploy: compile transcompile
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(COMPILED_RESOURCE_FILES) \
		$(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/assets
	cp -vf $(addprefix ./assets/, $(ASSETS)) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/assets
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/demo
	cp -vf $(addprefix ./demo/, $(DEMO)) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/demo
	cp -vfr i18n $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname ".git" -prune \
		-exec rm -Rf {} \;

derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

zip: deploy dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins; zip -9r $(CURDIR)/$(PLUGINNAME).zip \
		$(PLUGINNAME)

package: compile
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package.	"
	@echo "------------------------------------"
	rm -f $(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	echo "Created package: $(PLUGINNAME).zip"

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x scripts/update-strings.sh
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LRELEASE) $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

clean:
	@echo
	@echo "------------------------------------"
	@echo "Removing uic and rcc generated files"
	@echo "------------------------------------"
	rm $(COMPILED_UI_FILES) $(COMPILED_RESOURCE_FILES)

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc . || true

pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 \
		--exclude $(PEP8EXCLUDE) . || true
	@echo "-----------"
	@echo "Ignored in PEP8 check:"
	@echo $(PEP8EXCLUDE)
