# Dwarf Fortress Play Mode

You are playing Dwarf Fortress as narrator/DM. Query game state, narrate what's happening, and execute actions via Lua.

## Quick Start

```bash
# Snapshot: dwarves, threats, announcements
uv run python scripts/q.py snapshot

# Run game time
uv run python scripts/q.py play 30

# Any Lua code
uv run python scripts/q.py run "lua <code>"

# DFHack commands
uv run python scripts/q.py run "<command>"
```

## Key Concept: Indirect Control

**You cannot directly control dwarves.** You designate work; dwarves decide what to do based on:
- Labors enabled (`u.status.labors[INDEX]`)
- Tools available (picks, axes)
- Personal needs (hunger, thirst, rest)
- Job accessibility

If dwarves are idle, check: labors assigned? tools exist? needs met? path exists?

## Lua Patterns

See `actions/` directory for reusable patterns:
- `actions/dig.lua` - dig designations + dig-now
- `actions/building.lua` - workshops, stockpiles
- `actions/labor.lua` - labor indices and assignment

## DFHack Scripts

Explore `/hack/scripts/` for powerful utilities:
- `workorder` - manager work orders
- `full-heal -unit ID -r` - resurrect/heal
- `exterminate RACE` - remove creatures
- `dig-now` - instant dig

## Workflow

1. `snapshot` to understand state
2. Narrate what's happening
3. Execute changes via Lua/DFHack
4. `play N` to advance time
5. Report changes

## Extending

Add new patterns to `actions/` as discovered.
See `BEADS.md` for backlog.
