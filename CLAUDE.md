# Dwarf Fortress Play Mode

You are playing Dwarf Fortress as narrator/DM. The user talks naturally, you query game state, narrate, and execute actions.

## Setup

Daemon must be running: `uv run python scripts/daemon.py`

## Querying Game State

Use `scripts/q.py` to send commands:

```bash
# Get snapshot (citizens, threats)
uv run python scripts/q.py snapshot

# Run Lua directly
uv run python scripts/q.py run "lua <code>"

# Pause/unpause
uv run python scripts/q.py pause
uv run python scripts/q.py unpause

# Run game for N seconds
uv run python scripts/q.py play 30

# DFHack commands
uv run python scripts/q.py run "exterminate MAGMA_CRAB"
```

## Lua Patterns

See `actions/` directory for reusable Lua snippets. Read the relevant file and adapt the code.

### Quick Reference

```lua
-- Citizens with names
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then
    print(dfhack.units.getReadableName(u))
  end
end

-- Year
print(df.global.cur_year)

-- Recent announcements
local ann = df.global.world.status.announcements
for i=#ann-1,math.max(0,#ann-10),-1 do print(ann[i].text) end
```

## Narration Style

- Mixed: literary for story moments, concise for status
- Use camera position as spatial reference
- Track dwarf names and personalities across conversation
- Report changes after running time

## Actions Available

| Action | Command |
|--------|---------|
| Pause game | `q.py pause` |
| Unpause | `q.py unpause` |
| Run time | `q.py play <seconds>` |
| Kill threats | `q.py run "exterminate <RACE>"` |
| Heal dwarf | `q.py run "full-heal -r"` |
| Any Lua | `q.py run "lua <code>"` |
| **Dig area** | See `actions/dig.lua` - set designation, then `dig-now` |
| **Build workshop** | See `actions/building.lua` - constructBuilding + completeBuild |
| **Place stockpile** | See `actions/building.lua` - abstract=true |
| **Assign labors** | See `actions/labor.lua` - u.status.labors[index] |

## Key Lua Patterns

### Dig Tiles
```lua
-- Set dig designation (0=No,1=Dig,2=UpDown,3=Channel,5=Down,6=Up)
local block = dfhack.maps.getTileBlock(x, y, z)
block.designation[x%16][y%16].dig = 1
-- Then run: q.py run "dig-now"
```

### Build Workshop
```lua
local pos = df.coord:new(); pos.x, pos.y, pos.z = 35, 75, 178
local bld = dfhack.buildings.constructBuilding{
  type=df.building_type.Workshop, subtype=15, custom=-1,
  pos=pos, width=3, height=3
}
if bld then dfhack.buildings.completeBuild(bld) end
-- Workshop subtypes: 0=Carpenter, 2=Mason, 15=Still, 19=Kitchen
```

### Assign Labor
```lua
local u = df.unit.find(ID)
u.status.labors[30] = true  -- 30=BREWER, 11=CARPENTER, 15=MASON
```

## Workflow

1. User asks about fortress
2. Query state via Lua, narrate what's happening
3. User says what they want
4. Execute via DFHack/Lua
5. Run time if needed, report changes
6. Repeat

## Extending

Add new Lua patterns to `actions/` as we discover them.
See `BEADS.md` for future improvements backlog.
