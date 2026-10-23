PY = .venv/bin/python
.PHONY: setup lint test bench demo build
setup:
	python3 -m venv .venv
	$(PY) -m pip install -e . -r requirements-dev.txt
	npm --prefix apps/web ci
build:
	npm --prefix apps/web run build
lint:
	.venv/bin/ruff check src tests scripts
	.venv/bin/ruff format --check src tests scripts
	npm --prefix apps/web run lint
	node --check sdk/node/index.mjs
test:
	$(PY) scripts/local.py test
bench:
	$(PY) scripts/local.py bench
demo: setup build
	$(PY) scripts/local.py serve
