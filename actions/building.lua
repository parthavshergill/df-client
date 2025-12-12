-- Building placement via Lua
-- Run via: q.py run "lua <code>"

-- Workshop types:
-- 0=Carpenters, 1=Farmers, 2=Masons, 3=Craftsdwarfs, 4=Jewelers
-- 5=MetalsmithsForge, 6=MagmaForge, 7=Bowyers, 8=Mechanics, 9=Siege
-- 10=Butchers, 11=Leatherworks, 12=Tanners, 13=Clothiers, 14=Fishery
-- 15=Still, 16=Loom, 17=Quern, 18=Kennels, 19=Kitchen
-- 20=Ashery, 21=Dyers, 22=Millstone, 23=Custom, 24=Tool

-- Place a workshop (3x3)
-- NOTE: completeBuild() doesn't fully complete - dwarves must build OR use construction_stage=3
local pos = df.coord:new()
pos.x, pos.y, pos.z = 35, 75, 178
local bld, err = dfhack.buildings.constructBuilding{
  type = df.building_type.Workshop,
  subtype = 15,  -- Still
  custom = -1,
  pos = pos,
  width = 3,
  height = 3
}
if bld then
  -- Option 1: Let dwarves build it (creates ConstructBuilding job)
  dfhack.buildings.completeBuild(bld)

  -- Option 2: Instant completion (skip dwarf construction)
  bld.construction_stage = 3

  print("Built Still workshop, ID:", bld.id)
else
  print("Error:", err)
end

-- Find building by ID (robust - better than indexing buildings.all)
local ws = df.building.find(3)  -- returns building with id=3 or nil

-- Common workshops:
-- Still (brewing): subtype=15
-- Carpenters: subtype=0
-- Masons: subtype=2
-- Craftsdwarfs: subtype=3
-- Kitchen: subtype=19
-- Butchers: subtype=10

-- =============================================================================
-- STOCKPILES: Two-step process required!
-- =============================================================================
-- Step 1: Create stockpile via Lua
-- Step 2: Configure via DFHack "stockpiles import" command (REQUIRED!)
--
-- IMPORTANT: Setting sp.settings.flags.X = true is NOT enough!
-- You MUST use "stockpiles import library/<preset> -s <ID>" to configure.

-- Step 1: Create the stockpile structure
local sp, err = dfhack.buildings.constructBuilding{
  type = df.building_type.Stockpile,
  pos = {x=45, y=75, z=178},
  width = 5,
  height = 5,
  abstract = true
}
if sp then
  dfhack.buildings.completeBuild(sp)
  print("Created stockpile ID:", sp.id)
  -- Step 2: MUST run separately via q.py:
  -- q.py run "stockpiles import library/all -s <ID>"
else
  print("Error:", err)
end

-- Library presets (use with: stockpiles import library/<name> -s <ID>)
-- all              - Everything except refuse/corpses (most useful!)
-- cat_food         - Food and drink
-- cat_weapons      - Weapons
-- cat_armor        - Armor
-- cat_ammo         - Ammo (bolts, arrows)
-- cat_furniture    - Furniture
-- cat_stone        - Stone
-- cat_wood         - Wood
-- cat_cloth        - Cloth
-- cat_leather      - Leather
-- cat_bars_blocks  - Metal bars, blocks
-- cat_gems         - Gems
-- cat_finished_goods - Crafts, tools
-- cat_refuse       - Refuse (bones, shells)
-- cat_corpses      - Corpses
-- cat_animals      - Animals in cages/traps
-- cat_coins        - Coins
-- cat_sheets       - Paper, parchment
--
-- Specialized presets:
-- booze, seeds, plants, preparedmeals
-- metalbars, ironbars, steelbars, coal
-- metalweapons, metalarmor, bolts
-- roughgems, cutgems
-- See: q.py run "stockpiles list" for full list

-- Example: Create and configure a weapons stockpile
-- lua local sp=dfhack.buildings.constructBuilding{type=df.building_type.Stockpile,pos={x=85,y=96,z=151},width=4,height=4,abstract=true}; if sp then dfhack.buildings.completeBuild(sp); print('ID:',sp.id) end
-- Then: stockpiles import library/cat_weapons -s <ID>

-- List existing buildings
for i, b in ipairs(df.global.world.buildings.all) do
  print(b.id, df.building_type[b:getType()], b.centerx, b.centery, b.z)
end

-- Find building at position
local bld = dfhack.buildings.findAtTile({x=40, y=80, z=178})
if bld then print("Found:", bld.id) end

-- Remove building
-- dfhack.buildings.deconstruct(bld)
