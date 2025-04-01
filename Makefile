deps.lock:
	pip freeze | sort > requirements.txt

serve:
	cd src && python app.py
