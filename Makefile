deps.lock:
	pip freeze | sort > requirements.txt

deps.install:
	pip install -r requirements.txt

serve:
	cd src/ && flask run --debug

test:
	python -m unittest src.tests.integration.test_api_endpoints

test.pytest:
	pytest

test.pytest.verbose:
	pytest -v

test.coverage:
	pytest --cov=src

test.coverage.html:
	pytest --cov=src --cov-report=html
