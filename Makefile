MODULE_NAME=mara_db


all:
	# builds virtual env. and starts install in it
	make .venv/bin/python
	make install


install:
	# install of module
	.venv/bin/pip install .


test:
	make .venv/bin/python
	# test of module
	.venv/bin/pip install .[test]
	make tests/local_config.py
	.venv/bin/pytest


clean:
	# clean up
	rm -rf .venv/ build/ dist/ ${MODULE_NAME}.egg-info/ .pytest_cache/ .eggs/


.PYTHON3:=$(shell PATH='$(subst $(CURDIR)/.venv/bin:,,$(PATH))' which python3)

.venv/bin/python:
	mkdir -p .venv
	cd .venv && $(.PYTHON3) -m venv --copies --prompt='[$(shell basename `pwd`)/.venv]' .

	.venv/bin/python -m pip install --upgrade pip

tests/local_config.py:
	cp -v tests/local_config.py.example tests/local_config.py
	@ >&2 echo '!!! copied tests/local_config.py.example to tests/local_config.py. Please check'