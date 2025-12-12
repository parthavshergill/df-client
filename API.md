# Technical Reference

Low-level API for interacting with Dwarf Fortress via DFHack.

## Critical: Game Engine Integration

**Direct data modification bypasses game logic and may be reset.** Use these functions to properly trigger the game engine:

```lua
-- After setting designations (dig, chop, etc.)
dfhack.job.checkDesignationsNow()   -- Creates jobs AND assigns workers

-- After creating building construction jobs
dfhack.job.checkBuildingsNow()      -- Creates jobs for buildings

-- To manually assign a worker to a job
dfhack.job.addWorker(job, unit)     -- Forces unit to work on job
```

## Proper Patterns

### Designate Digging (dwarves complete)
```lua
local x, y, z = 95, 93, 175
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.designation[bx][by].dig = 1  -- 1=mine, 2=UD-stair, 3=channel, 5=D-stair
block.flags.designated = true
dfhack.job.checkDesignationsNow()  -- CRITICAL: triggers job creation
```

### Add Workshop Job (proper method)
```lua
-- Find workshop
local ws = df.building.find(4)  -- by ID

-- Create job with item requirements
local job = df.job:new()
job.job_type = df.job_type.MakeBarrel  -- or use integer 125

-- Add material filter (REQUIRED for most jobs)
local jitem = df.job_item:new()
jitem.item_type = df.item_type.WOOD
jitem.quantity = 1
jitem.vector_id = df.job_item_vector_id.WOOD
job.job_items.elements:insert('#', jitem)

dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)
-- Dwarf with correct labor will pick it up automatically
```

### Build Workshop/Building (dwarves complete)
```lua
local bld = dfhack.buildings.constructBuilding{
  type = df.building_type.Workshop,
  subtype = df.workshop_type.Still,  -- or integer
  pos = {x=96, y=88, z=178},
  width = 3, height = 3
}
-- Building is created with ConstructBuilding job
-- Dwarves will gather materials and build
```

### Complete Building Instantly (cheat)
```lua
bld:setBuildStage(bld:getMaxBuildStage())
dfhack.buildings.completeBuild(bld)
```

### Labor Assignment
```lua
for _, u in ipairs(dfhack.units.getCitizens()) do
  u.status.labors[df.unit_labor.MINE] = true
  u.status.labors[df.unit_labor.PLANT] = true
end
```

## Job API Functions

| Function | Purpose |
|----------|---------|
| `dfhack.job.linkIntoWorld(job)` | Add job to world job list |
| `dfhack.job.assignToWorkshop(job, ws)` | Link job to workshop |
| `dfhack.job.addWorker(job, unit)` | Assign worker to job |
| `dfhack.job.removeJob(job)` | Cancel job |
| `dfhack.job.getHolder(job)` | Get building holding job |
| `dfhack.job.getWorker(job)` | Get unit performing job |
| `dfhack.job.checkDesignationsNow()` | Create jobs from designations |
| `dfhack.job.checkBuildingsNow()` | Create jobs for buildings |

## Workshop Types (df.workshop_type)

| ID | Type | Products |
|----|------|----------|
| 0 | Carpenters | Beds, barrels, bins, furniture |
| 2 | Masons | Stone furniture, blocks |
| 3 | Craftsdwarfs | Crafts, totems |
| 10 | Butchers | Meat |
| 15 | Still | Alcohol |
| 19 | Kitchen | Meals |

## Job Types (df.job_type)

| ID | Job |
|----|-----|
| 69 | ConstructBed |
| 70 | ConstructThrone (chair) |
| 72 | ConstructTable |
| 67 | ConstructDoor |
| 113 | BrewDrink |
| 125 | MakeBarrel |
| 126 | MakeBucket |

## Dig Designation Values

| Value | Result |
|-------|--------|
| 1 | Mine → Floor |
| 2 | UD-Stair |
| 3 | Channel |
| 5 | D-Stair |
| 6 | U-Stair |

## Labor Types (df.unit_labor)

| Labor | Purpose |
|-------|---------|
| MINE | Mining (needs pick) |
| PLANT | Farming |
| BREWER | Brewing |
| CARPENTER | Woodworking |
| MASON | Stoneworking |
| HAUL_FOOD | Moving food |

## Key Limitations

1. **Stair upgrades**: Can't upgrade existing stairs via CarveUpDownStaircase
2. **Designations on floors**: Can't dig floors, only walls
3. **Direct tiletype changes**: May be reset by game engine
4. **Work orders**: Require manager noble (skip them, add jobs directly)

## DFHack Connection

- **Host**: `127.0.0.1:5000` (TCP, auto-starts with game)
- **Protocol**: Protobuf RPC

## Global Tables

| Table | Contents |
|-------|----------|
| `df.global.world.units.active` | All units |
| `df.global.world.buildings.all` | All buildings |
| `df.global.world.items.all` | All items |
| `df.global.world.jobs.list` | Active jobs (linked list) |
