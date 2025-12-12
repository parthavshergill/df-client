# Dwarf Fortress Play Mode

You are playing Dwarf Fortress as narrator/DM. Designate work for dwarves; they act autonomously.

## Commands

```bash
uv run python scripts/q.py daemon              # Start first
uv run python scripts/q.py snapshot [radius]   # Camera-centered view (default 100)
uv run python scripts/q.py tick N              # Advance N game ticks

# Designations (dwarves will complete these)
uv run python scripts/q.py dig x1 y1 z x2 y2 [type]      # mine, stair_down, channel, etc.
uv run python scripts/q.py build <type> x y z             # carpenter, still, mason, etc.
uv run python scripts/q.py stockpile x y z w h <preset>   # all, food, stone, etc.
uv run python scripts/q.py labor <name> <labor> on|off    # MINE, PLANT, BREWER, etc.

# Cheats
uv run python scripts/q.py dig-now             # Instant dig
uv run python scripts/q.py run "full-heal -all"
uv run python scripts/q.py run "lua ..."       # Raw Lua for anything else
```

## Adding Jobs to Workshops (Primary Method)

Work orders (`order` command) require a **manager noble** - skip them. Add jobs directly:

```lua
-- Find workshop (0=Carpenter, 15=Still, 2=Mason, etc.)
local ws; for i,b in ipairs(df.global.world.buildings.all) do
  if b:getSubtype() == 0 and df.building_workshopst:is_instance(b) then ws = b; break end
end

-- Create and assign job (125=MakeBarrel, 113=ProcessPlantsBarrel/brew)
local job = df.job:new()
job.job_type = 125
dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)
```

Key job types: MakeBarrel=125, ProcessPlantsBarrel=113 (brewing), MakeBed=?, ConstructTable=?
See `API.md` for full list.

## Key Concept

**You cannot directly control dwarves.** You designate work; they decide what to do based on labors enabled, tools available, and personal needs.

## Time

- `tick 100-500` at a time (dwarves can starve during long advances)
- ~1200 ticks = 1 day, ~100,800 ticks = 1 season
- Enable timestream: `run "enable timestream"` then `run "timestream set fps 100"`

## Lua Patterns

- `actions/` — Verified working patterns
- `experiments/` — Testing new patterns (promote to actions/ when verified)

## References

- `JOURNAL.md` — Session log (current state)
- `GUIDE.md` — Gameplay strategies
- `API.md` — Technical reference
