# AGENTS.md

Project conventions for editing this codebase. Follow these strictly.

## Communication
- Low verbosity. Answer concisely; omit filler.
- No emojis unless requested.

## Code style
- KISS, DRY, SOLID — keep it simple, avoid duplication, single responsibility.
- Split code into small functions; one function = one purpose.
- Keep functions/methods <= 25 lines.
- Clean, modern 2026 Python: type hints, `dataclasses` where sensible.
- Use Ruff for linting (see `pyproject.toml`).
- Lambdas / anonymous functions only for tiny, real helpers that improve readability — never for logic-heavy bodies.

## Structure
- Split code into directories by responsibility.
- Put all helpers in `./src/helpers`.
- Design patterns only when they genuinely reduce duplication / generalize code — don't over-engineer.

## Verification
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`