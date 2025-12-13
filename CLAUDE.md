# Dwarf Fortress Play Mode

You are playing Dwarf Fortress as narrator/DM. Designate work for dwarves; they act autonomously.

## Core Philosophy

**You can only designate tasks.** Dwarves decide when to eat, drink, sleep, and which jobs to take based on their needs, skills, and available tools. Don't micromanage - set up the work and let them live.

## Commands

```bash
uv run python scripts/q.py daemon              # Start first
uv run python scripts/q.py snapshot [radius]   # Camera-centered view (default 100)
uv run python scripts/q.py tick N              # Advance N game ticks
uv run python scripts/q.py dig-now             # Instant dig (cheat for setup)
uv run python scripts/q.py run "lua ..."       # Raw Lua for anything else
```

## Level 2 DFHack APIs (Use These!)

Direct memory manipulation bypasses game logic. Use helper functions:

```lua
-- After designations (dig, chop, etc.)
dfhack.job.checkDesignationsNow()   -- Creates jobs AND assigns workers

-- Workshop jobs (use createLinked, NOT df.job:new())
local job = dfhack.job.createLinked()
job.job_type = 125  -- MakeBarrel
dfhack.job.assignToWorkshop(job, workshop)

-- Buildings
dfhack.buildings.constructBuilding{type=..., pos=...}
dfhack.job.checkBuildingsNow()
```

## Common Patterns

### Designate Digging
```lua
local block = dfhack.maps.getTileBlock(x, y, z)
block.designation[x%16][y%16].dig = df.tile_dig_designation.Default
block.flags.designated = true
dfhack.job.checkDesignationsNow()
```

### Add Workshop Job
```lua
local ws = df.building.find(ID)
local job = dfhack.job.createLinked()
job.job_type = 125  -- MakeBarrel=125, BrewDrink=113, ConstructBed=69
job.mat_type = -1
local jitem = df.job_item:new()
jitem.item_type = -1
jitem.mat_type = -1
jitem.mat_index = -1
jitem.quantity = 1
jitem.vector_id = df.job_item_vector_id.WOOD
job.job_items.elements:insert('#', jitem)
dfhack.job.assignToWorkshop(job, ws)
```

### Enable Labors
```lua
for _,u in ipairs(dfhack.units.getCitizens()) do
  u.status.labors[df.unit_labor.MINE] = true
  u.status.labors[df.unit_labor.PLANT] = true
  u.status.labors[df.unit_labor.BREWER] = true
  u.status.labors[df.unit_labor.CUTWOOD] = true
end
```

## Time

- `tick 100-500` for quick checks
- `tick 1000-5000` for meaningful progress
- ~1200 ticks = 1 day

## References

- `API.md` — Full technical reference
- `GUIDE.md` — Gameplay strategies
- `actions/` — Reusable Lua patterns
