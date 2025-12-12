# Dwarf Fortress Play Mode

You are playing Dwarf Fortress as narrator/DM. Designate work for dwarves; they act autonomously.

## Orchestration Loop

1. **Snapshot** — `q.py snapshot` to see state
2. **Analyze** — What do dwarves need? What work should be done?
3. **Designate** — Dig, build, add jobs, enable labors
4. **Tick** — `q.py tick N` to let dwarves act
5. **Repeat**

## Commands

```bash
uv run python scripts/q.py daemon              # Start first
uv run python scripts/q.py snapshot [radius]   # Camera-centered view
uv run python scripts/q.py tick N              # Advance N ticks
uv run python scripts/q.py dig x1 y1 z x2 y2 [type]   # Designate dig
uv run python scripts/q.py build <type> x y z         # Build workshop
uv run python scripts/q.py run "lua ..."              # Raw Lua
```

## Key Concept

**You cannot directly control dwarves.** You designate work; they decide what to do based on labors, tools, and needs.

## Triggering Game Engine (Critical!)

Direct data modification does NOT trigger game logic. After setting designations:
```lua
dfhack.job.checkDesignationsNow()  -- Creates jobs from designations, assigns workers
dfhack.job.checkBuildingsNow()     -- Creates jobs for buildings
dfhack.job.addWorker(job, unit)    -- Manually assign worker to job
```

## Dwarf Needs

Dwarves don't auto-eat/drink in this setup. Use these workarounds:
- `run "full-heal -all"` — Reset all hunger/thirst/sleep to 0
- Or assign Eat jobs manually (see `experiments/11-orchestration.lua`)

## References

- `API.md` — Lua patterns, job types, building types
- `experiments/` — Tested patterns (see README for status)
- `GUIDE.md` — Gameplay strategies
- `JOURNAL.md` — Session log
