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

## Turn resolution
- The player acts first, then each NPC acts in order, each against live world state (like Brogue/Rogue/Crawl).
- Resolve actions synchronously in systems; never defer commands that later actors must observe.
- Movement and bumping are 4-directional only (no diagonals).

## Verification
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`