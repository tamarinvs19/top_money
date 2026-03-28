# Sample AGENTS.md file

## Dev environment tips
- Use `uv` python environment
- Make migrations: `uv run python manage.py makemigrations`
- Migrate database: `uv run python manage.py migrate`
- Run tests: `uv run python manage.py test`
- Do not use `vycheslav` pattern anywhere

## Testing instructions
- Find the CI plan in the .github/workflows folder.
- Fix any test or type errors until the whole suite is green.
- Add or update tests for the code you change, even if nobody asked.

## PR instructions
- Always run `uv run python manage.py test` before pushing.
- Always check requirements and update `requirements.txt` if it's necessary

## Code style
- Prefer all imports on the top of the file
- Single quote better then double
- Add type annotations where necessary
