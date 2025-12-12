-- experiments/04-farming.lua
-- Status: working
-- Last tested: 2024-12-12

-- =============================================================================
-- PATTERN: Create farm plot (requires soil/mud floor)
-- =============================================================================
-- Usage: q.py run "lua <one-liner>"
local fp = dfhack.buildings.constructBuilding{
  type = df.building_type.FarmPlot,  -- type 4
  pos = {x=91, y=91, z=177},
  width = 3, height = 3
}
dfhack.buildings.completeBuild(fp)
fp.construction_stage = 3
-- Returns: building ID

-- =============================================================================
-- PATTERN: Set plant for all seasons
-- =============================================================================
-- plant_id[0]=spring, [1]=summer, [2]=autumn, [3]=winter
-- MUSHROOM_HELMET_PLUMP = 173 (grows underground all seasons)
local fp = df.building.find(1)
for i = 0, 3 do fp.plant_id[i] = 173 end

-- =============================================================================
-- PATTERN: Find plant ID by name
-- =============================================================================
for i, p in ipairs(df.global.world.raws.plants.all) do
  if p.id:find("PLUMP") then print(i, p.id) end
end
-- Common: 173=MUSHROOM_HELMET_PLUMP

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Check soil type at position
-- [ ] Fertilization (potash)
-- [ ] Above-ground vs underground plants
