# Session Journal (1-line entries)

## Year 100 Summer - Fresh Embark

**Setup:**
- 7 dwarves arrived, shelter dug at z=176 (stone layer)
- Staircase: z=178 (surface) → z=177 (soil) → z=176 (stone)
- Carpenter workshop (id=2) at 98,92,176
- Still workshop (id=3) at 98,96,176
- Stockpile (id=1) at 93,93,176, preset=all

**Verified Working Patterns:**
- `df.job:new()` + `linkIntoWorld()` + `assignToWorkshop()` for workshop jobs
- Integer job types (113=brew, 125=barrel) - enum names may not exist
- `df.building.find(ID)` for robust building lookup
- `block.tiletype[bx][by] = df.tiletype.ConstructedStairU` to change existing tiles
- `b.construction_stage = 3` for instant building completion

**Known Issues:**
- `completeBuild()` doesn't fully complete - use construction_stage=3
- Dig designations only work on walls, not existing floors
- Port 5000 conflicts with macOS AirPlay Receiver
- `workorder` command requires manager noble
