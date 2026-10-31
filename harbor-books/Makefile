CFG = python3 scripts/drill_config.py
PY ?= .venv/bin/python

.PHONY: up setup seed bench test reset record report submit checkpoint

setup:
	@sh -c "$$($(CFG) setup_cmd)"

up: setup
	@[ -d .git ] || sh scripts/init-git.sh
	@python3 scripts/drill_log.py once make "make up"
	@[ -f $$($(CFG) db_file) ] || sh -c "$$($(CFG) seed_cmd)"
	sh -c "$$($(CFG) start_cmd)"

seed: setup
	sh -c "$$($(CFG) seed_cmd)"

bench: setup
	$(PY) bench.py

test: setup
	$(PY) scripts/run_tests.py

reset:
	@if [ -d .git ]; then git reset --hard $$($(CFG) start_tag) && git clean -fdx -e '*.db' -e .venv; fi
	@$(MAKE) --no-print-directory seed

record:
	./scripts/record.sh

submit:
	python3 scripts/submit.py

report: submit

checkpoint:
	python3 scripts/drill_log.py checkpoint
