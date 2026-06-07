.PHONY: install run test
install:; pip install -r requirements.txt
run:; python -m stockagent.cli
test:; pytest -q
