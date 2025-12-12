-- Labor assignment via Lua
-- Run via: q.py run "lua <code>"

-- Labor indices:
-- 0=MINE, 1=HAUL_STONE, 2=HAUL_WOOD, 3=HAUL_BODY, 4=HAUL_FOOD
-- 5=HAUL_REFUSE, 6=HAUL_ITEM, 7=HAUL_FURNITURE, 8=HAUL_ANIMALS, 9=CLEAN
-- 10=CUTWOOD, 11=CARPENTER, 12=STONECUTTER, 13=STONE_CARVER, 14=ENGRAVER
-- 15=MASON, 16=ANIMALTRAIN, 17=ANIMALCARE, 18=DIAGNOSE, 19=SURGERY
-- 20=BONE_SETTING, 21=SUTURING, 22=DRESSING_WOUNDS, 23=FEED_WATER_CIVILIANS
-- 24=RECOVER_WOUNDED, 25=BUTCHER, 26=TRAPPER, 27=DISSECT_VERMIN
-- 28=LEATHER, 29=TANNER, 30=BREWER, 31=SOAP_MAKER, 32=WEAVER
-- 33=CLOTHESMAKER, 34=MILLER, 35=PROCESS_PLANT, 36=MAKE_CHEESE
-- 37=MILK, 38=COOK, 39=PLANT, 40=HERBALIST

-- Enable/disable labor for a unit
local u = df.global.world.units.active[0]
u.status.labors[30] = true  -- Enable brewing
u.status.labors[11] = true  -- Enable carpentry
print("Enabled brewing and carpentry for", dfhack.units.getReadableName(u))

-- Enable labor by name (use df.unit_labor enum)
u.status.labors[df.unit_labor.MINE] = true

-- List enabled labors for a unit
for i = 0, 80 do
  if u.status.labors[i] then
    local name = df.unit_labor[i]
    if name then print(name) end
  end
end

-- Find unit by name fragment
for i, u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then
    local name = dfhack.units.getReadableName(u)
    if name:find("Logem") then
      print("Found:", name, "ID:", u.id)
      -- Do something with this unit
    end
  end
end

-- Enable all hauling labors
local hauling = {1, 2, 3, 4, 5, 6, 7, 8}
for _, labor in ipairs(hauling) do
  u.status.labors[labor] = true
end

-- Disable all labors except mining
for i = 0, 80 do
  u.status.labors[i] = (i == 0)  -- Only mining enabled
end
