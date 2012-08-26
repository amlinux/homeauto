.PHONY: all syncdb resetDatabase

all:

syncdb:
	django-admin syncdb --pythonpath=`pwd`

resetDatabase:
	mysql -e 'drop database if exists hauto'
	mysql -e 'create database hauto'
	make syncdb

clean:
	find -name '*.pyc' -exec rm {} \;
