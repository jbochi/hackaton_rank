.PHONY: deploy

deploy:
	python run.py
	tsuru app-deploy -a top index.html
