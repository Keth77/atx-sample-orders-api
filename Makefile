.PHONY: test lint unit node

test: unit node lint

unit:
	python -m pytest -q tests/unit

node:
	node --test tests/node/*.test.js

lint:
	cfn-lint template.yaml
