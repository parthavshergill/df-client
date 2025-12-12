-- Building placement via Lua
-- Run via: q.py run "lua <code>"

-- Workshop types:
-- 0=Carpenters, 1=Farmers, 2=Masons, 3=Craftsdwarfs, 4=Jewelers
-- 5=MetalsmithsForge, 6=MagmaForge, 7=Bowyers, 8=Mechanics, 9=Siege
-- 10=Butchers, 11=Leatherworks, 12=Tanners, 13=Clothiers, 14=Fishery
-- 15=Still, 16=Loom, 17=Quern, 18=Kennels, 19=Kitchen
-- 20=Ashery, 21=Dyers, 22=Millstone, 23=Custom, 24=Tool

-- Place and complete a workshop (3x3)
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
  dfhack.buildings.completeBuild(bld)
  print("Built Still workshop, ID:", bld.id)
else
  print("Error:", err)
end

-- Common workshops:
-- Still (brewing): subtype=15
-- Carpenters: subtype=0
-- Masons: subtype=2
-- Craftsdwarfs: subtype=3
-- Kitchen: subtype=19
-- Butchers: subtype=10

-- Place stockpile (abstract, no items needed)
local pos = df.coord:new()
pos.x, pos.y, pos.z = 45, 75, 178
local sp, err = dfhack.buildings.constructBuilding{
  type = df.building_type.Stockpile,
  pos = pos,
  width = 5,
  height = 5,
  abstract = true
}
if sp then
  dfhack.buildings.completeBuild(sp)
  -- Configure what stockpile accepts
  sp.settings.flags.food = true
  -- sp.settings.flags.furniture = true
  -- sp.settings.flags.stone = true
  print("Built food stockpile, ID:", sp.id)
else
  print("Error:", err)
end

-- List existing buildings
for i, b in ipairs(df.global.world.buildings.all) do
  print(b.id, df.building_type[b:getType()], b.centerx, b.centery, b.z)
end

-- Find building at position
local bld = dfhack.buildings.findAtTile({x=40, y=80, z=178})
if bld then print("Found:", bld.id) end

-- Remove building
-- dfhack.buildings.deconstruct(bld)
