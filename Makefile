install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	python -m pytest -vv test_*.py 

format:
	black *.py 

lint:
	pylint --disable=R,C,E1120 *.py src/*.py src/**/*.py

all: install format lint test