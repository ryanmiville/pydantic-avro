.PHONY: check

check:
	uv run pytest
	uv run ruff check --fix
	uv run ty check --fix
