# frogue

An open-source terminal roguelike written in Python, built on the [Hive](vendor/hive) ECS runtime. Descend 5 procedurally generated dungeon floors, fight a cast of monster archetypes, and reach the exit stair to escape.

## Features

- Procedurally generated dungeons with field-of-view exploration
- Classic turn-based roguelike combat with bump attacks and ranged foes
- Three monster archetypes: `HUNTER`, `RANGED`, and position-remembering `TRACKER`
- Persistent hit points across floor transitions and a scoring system
- Save and load your run at any time
- Win by reaching the exit stair on depth 5

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Run

```sh
uv run python -m frogue
```

## Controls

| Key | Action |
| --- | --- |
| `w` `a` `s` `d` | Move (4-directional) |
| `e` | Interact (use stairs) |
| `S` | Save game to `save.json` |
| `q` | Quit |

### Screens

- **Start**: `Enter` new game, `L` load save, `Q` quit
- **Death / Victory**: `R` restart, `S` start screen, `Q` quit

## Gameplay

- The player acts first, then every monster acts in order against the live world state.
- **Enemy archetypes**: `HUNTER` chases and bumps, `RANGED` shoots from a distance, `TRACKER` remembers the player's last seen position.
- **HP** carries across floor transitions; death is permanent until you restart.
- **Score**: `max(0, kills*10 + depth*50 - turns)`; only player-caused kills count.
- **Win**: reach the exit stair on depth 5.

## Development

```sh
uv run ruff check .   # lint
uv run ruff format .  # format
uv run pytest         # tests
```

## Project layout

- `src/frogue/` — game code
  - `core/` — ECS systems, components, resources (movement, bump, AI, FOV, save/load)
  - `dungeon/` — procedural generation and stair placement
  - `render/` — curses rendering
- `vendor/hive/` — vendored ECS runtime (world, systems, snapshot serialization)
- `tests/` — pytest suite
