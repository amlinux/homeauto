.PHONY: all syncdb resetDatabase translations pot po mo js

all: translations

langs := ru-ru
mo_modules := homeauto
js_modules := homeautojs

# ============= MODULE: homeauto ===============
homeauto_sources := $(shell find . -name '*.py')
homeauto_mo_files := $(foreach lang,$(langs),locales/$(lang)/LC_MESSAGES/homeauto.mo)
homeauto_po_files := $(foreach lang,$(langs),locales/homeauto/$(lang).po)
locales/homeauto.pot: $(homeauto_sources)
	find . -name '*.py' > .src-files
	xgettext -d homeauto -f .src-files -L Python --copyright-holder=$(copyright) \
		--package-name=$(package_name) --package-version=$(package_version) \
		--force-po -kgettext_noop -s --omit-header --no-location
	rm .src-files
	mv homeauto.po locales/homeauto.pot
	mkdir -p locales/homeauto
locales/homeauto/%.po: locales/homeauto.pot
	msgmerge -U $@ $<
	touch $@
locales/%/LC_MESSAGES/homeauto.mo: locales/homeauto/%.po
	mkdir -p `dirname $@`
	msgfmt -o $@ $<

# ============= MODULE: homeautojs ===============
homeautojs_sources := $(shell find staticfiles/js/homeauto -name '*.js')
homeautojs_js_files := $(foreach lang,$(langs),staticfiles/js/gettext-$(lang).js)
homeautojs_po_files := $(foreach lang,$(langs),locales/homeautojs/$(lang).po)
locales/homeautojs.pot: $(homeautojs_sources)
	find . -name '*.py' > .src-files
	xgettext -d homeautojs -f .src-files -L Python --copyright-holder=$(copyright) \
		--package-name=$(package_name) --package-version=$(package_version) \
		--force-po -kgettext_noop -s --omit-header --no-location
	rm .src-files
	mv homeautojs.po locales/homeautojs.pot
	mkdir -p locales/homeautojs
locales/homeautojs/%.po: locales/homeautojs.pot
	msgmerge -U $@ $<
	touch $@
staticfiles/js/gettext-%.js: locales/homeautojs/%.po
	(echo -n 'var gt=new Gettext({"domain": "mg_constructor", "locale_data": {"mg_constructor": '; po2json $< ; echo '}})') > $@

translations: pot po mo js

modules := $(mo_modules) $(js_modules)
pot: $(foreach module,$(modules),locales/$(module).pot)
po: $(foreach module,$(modules),$($(module)_po_files))
mo: $(foreach module,$(mo_modules),$($(module)_mo_files))
js: $(foreach module,$(js_modules),$($(module)_js_files))

debug:
	@echo "POT Files: $(foreach module,$(modules),locales/$(module).pot)"
	@echo "PO Files: $(foreach module,$(modules),$($(module)_po_files))"
	@echo "MO Files: $(foreach module,$(mo_modules),$($(module)_mo_files))"
	@echo "JS Files: $(foreach module,$(js_modules),$($(module)_js_files))"

syncdb:
	django-admin syncdb --pythonpath=/home/aml/electronics/homeauto --settings=hautoweb.settings

resetDatabase:
	rm -f homeauto.db
	make syncdb

clean:
	find -name '*.pyc' -exec rm {} \;
