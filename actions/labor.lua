-- Labor assignment via Lua
-- Run via: q.py run "lua <code>"

-- Labor indices (key ones):
-- 0=MINE (needs pick)
-- 10=CUTWOOD (needs axe)
-- 11=CARPENTER, 15=MASON
-- 30=BREWER, 38=COOK, 39=PLANT (farming)
-- Hauling: 1-8 (HAUL_STONE, HAUL_WOOD, HAUL_BODY, HAUL_FOOD, etc.)
-- Use df.unit_labor enum: df.unit_labor.MINE, df.unit_labor.CUTWOOD, etc.

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
