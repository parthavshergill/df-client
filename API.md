# Technical Reference

Low-level API details for extending the df-client.

## Architecture

```
q.py (CLI) → TCP:5001 → DFDaemon → TCP:5000 → DFHack RemoteFortressReader
                                 ↘ Lua commands via run_command()
```

## Raw Lua Access

For operations not covered by high-level commands:

```bash
uv run python scripts/q.py run "lua <code>"
uv run python scripts/q.py run "<dfhack_command>"
```

## Lua Patterns

See `actions/` directory for examples. Key patterns:

### Dig Designation
```lua
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.designation[bx][by].dig = 1  -- 1=mine, 5=stair_down, 3=channel
```

### Change Existing Tile (when dig doesn't work)
Dig designations only work on WALLS, not existing floors. To change a floor:
```lua
local block = dfhack.maps.getTileBlock(x, y, z)
block.tiletype[x%16][y%16] = df.tiletype.ConstructedStairU  -- or StairD, StairUD
```

### Build Workshop
```lua
local bld = dfhack.buildings.constructBuilding{
  type = df.building_type.Workshop,
  subtype = 15,  -- Still
  pos = {x=35, y=75, z=178},
  width = 3, height = 3
}
-- NOTE: completeBuild() doesn't fully complete workshops!
dfhack.buildings.completeBuild(bld)  -- Creates job, dwarves must build
bld.construction_stage = 3           -- OR: instant completion (cheat)
```

### Find Building by ID
```lua
local ws = df.building.find(3)  -- robust lookup by building ID
```

### Labor Assignment
```lua
local u = df.global.world.units.active[0]
u.status.labors[df.unit_labor.MINE] = true
```

### Iterate Citizens
```lua
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) and dfhack.units.isAlive(u) then
    print(dfhack.units.getReadableName(u), u.pos.x, u.pos.y, u.pos.z)
  end
end
```

## Workshop Subtypes

| ID | Type |
|----|------|
| 0 | Carpenters |
| 2 | Masons |
| 3 | Craftsdwarfs |
| 10 | Butchers |
| 15 | Still |
| 19 | Kitchen |

## Job Types (df.job_type)

| ID | Job |
|----|-----|
| 113 | ProcessPlantsBarrel (brewing) |
| 125 | MakeBarrel |
| 126 | MakeBucket |
| 82 | MakeCrafts |
| 96 | MakeWeapon |
| 100 | MakeArmor |
| 184 | MakeCharcoal |
| 109 | MakeCheese |
| 110 | ProcessPlants |

### Direct Job Creation (skip work orders)

```lua
-- Find workshop by ID (robust)
local ws = df.building.find(3)  -- workshop with id=3

-- Create job with integer type (enum names may not work!)
local job = df.job:new()
job.job_type = 125  -- MakeBarrel (use integers, not df.job_type.X)
dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)
```

## Labor Indices

| ID | Labor |
|----|-------|
| 0 | MINE |
| 10 | CUTWOOD |
| 11 | CARPENTER |
| 15 | MASON |
| 30 | BREWER |
| 39 | PLANT |

Full list: `df.unit_labor` enum

## DFHack Connection

- **Host**: `127.0.0.1:5000` (TCP)
- **Protocol**: Protobuf RPC with length-prefixed messages
- **Handshake**: Send `DFHack?\n` + version(4 bytes LE)

### Troubleshooting: Port 5000 Conflict (macOS)

macOS AirPlay Receiver uses port 5000 by default. If DFHack can't connect:

1. **Option A:** Disable AirPlay Receiver
   - System Settings → General → AirDrop & Handoff → Turn off "AirPlay Receiver"

2. **Option B:** Use alternate port in DFHack console:
   ```
   remote-server start 5050
   ```
   Then update client to use port 5050.

## Key Global Tables

| Table | Contents |
|-------|----------|
| `df.global.world.units.active` | All units |
| `df.global.world.buildings.all` | All buildings |
| `df.global.world.items.all` | All items |
| `df.global.world.jobs.list` | Active jobs |
| `df.global.window_x/y/z` | Camera position |

### Move Camera
```lua
df.global.window_x = 95
df.global.window_y = 95
df.global.window_z = 176
```

## Useful DFHack Commands

```bash
dig-now                              # Complete dig designations
full-heal -all                       # Heal everyone
exterminate RACE                     # Remove creatures
stockpiles import library/all -s ID  # Configure stockpile
workorder '{"job":"X","amount":N}'   # Create work order
enable timestream                    # Speed up simulation
```
