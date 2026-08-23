.PHONY: install install-service install-bundle uninstall-service package check lint typecheck test shellcheck run clean

install:
	poetry install

install-service:
	./install.sh

install-bundle:
	./install.sh --bundle

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

package:
	poetry run pyinstaller aw-watcher-mic.spec --clean --noconfirm

run:
	poetry run aw-watcher-mic --testing --verbose

clean:
	rm -rf build dist
