.PHONY: install install-service uninstall-service check lint typecheck test shellcheck run

install:
	poetry install

install-service:
	./install.sh

uninstall-service:
	./install.sh --uninstall

check: lint typecheck test shellcheck

lint:
	poetry run ruff check aw_watcher_mic tests
	poetry run ruff format --check aw_watcher_mic tests

typecheck:
	poetry run mypy aw_watcher_mic

test:
	poetry run pytest -q

shellcheck:
	shellcheck install.sh

run:
	poetry run aw-watcher-mic --testing --verbose
