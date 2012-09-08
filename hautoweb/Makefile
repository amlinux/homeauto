.PHONY: all syncdb resetDatabase

all:

syncdb:
	django-admin syncdb --pythonpath=/home/aml/electronics/homeauto --settings=hautoweb.settings

resetDatabase:
	rm -f homeauto.db
	make syncdb

clean:
	find -name '*.pyc' -exec rm {} \;
