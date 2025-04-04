deps.lock:
	pip freeze | sort > requirements.txt

deps.install:
	pip install -r requirements.txt

serve:
	cd src/ && flask run --debug
