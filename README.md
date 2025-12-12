# df-client

Let Claude play Dwarf Fortress via DFHack.

## How It Works

Claude acts as narrator/DM: designates work (dig, build, farm) and dwarves act autonomously. The orchestration loop is: **Snapshot → Analyze → Designate → Tick → Repeat**.

## Requirements

- Dwarf Fortress with DFHack (DFHack RPC server auto-starts on port 5000)
- Python 3.11+ with uv

## Quick Start

```bash
# 1. Start DF with DFHack, load a save
# 2. Clone and setup
git clone <repo>
cd df-client
uv sync

# 3. Start daemon (connects to DFHack)
uv run python scripts/q.py daemon

# 4. Open Claude Code in this directory
# Claude reads CLAUDE.md for instructions
```

## CLI Commands

```bash
uv run python scripts/q.py snapshot [radius]   # Game state (camera-centered)
uv run python scripts/q.py tick N              # Advance N ticks
uv run python scripts/q.py dig x1 y1 z x2 y2   # Designate digging
uv run python scripts/q.py build <type> x y z  # Build workshop
uv run python scripts/q.py run "lua ..."       # Raw Lua/DFHack command
```

## Files

- `CLAUDE.md` — Instructions for Claude (read this first)
- `API.md` — Lua patterns, job types, building types
- `experiments/` — Tested Lua patterns with status
- `GUIDE.md` — Gameplay strategies

## Architecture

```
Claude Code ←→ q.py daemon ←→ DFHack RPC (port 5000) ←→ Dwarf Fortress
                (port 5001)
```
