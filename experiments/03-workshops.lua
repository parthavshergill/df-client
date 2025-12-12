-- experiments/03-workshops.lua
-- Status: working
-- Last tested: 2024-12-12

-- =============================================================================
-- PATTERN: Build workshop (designate, dwarf will build)
-- =============================================================================
-- Workshop types: 0=Carpenter, 2=Mason, 15=Still, etc.
local ws = dfhack.buildings.constructBuilding{
  type = df.building_type.Workshop,
  subtype = df.workshop_type.Still,
  pos = {x=96, y=88, z=178},
  width = 3, height = 3
}
-- Dwarves will gather materials and build (or use construction_stage=3 to cheat)

-- =============================================================================
-- PATTERN: Find workshop by type
-- =============================================================================
local found
for _, b in ipairs(df.global.world.buildings.all) do
  if df.building_workshopst:is_instance(b) and b:getSubtype() == df.workshop_type.Carpenters then
    found = b
    break
  end
end

-- =============================================================================
-- PATTERN: Add job to workshop (dwarf will perform)
-- =============================================================================
-- Requires job_item for materials (e.g., vector_id=18 for WOOD)
local ws = df.building.find(4)
local job = df.job:new()
job.job_type = 125  -- MakeBarrel
local jitem = df.job_item:new()
jitem.item_type = df.item_type.WOOD
jitem.quantity = 1
jitem.vector_id = 18  -- WOOD
job.job_items.elements:insert('#', jitem)
dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)

-- =============================================================================
-- PATTERN: Cancel/remove job
-- =============================================================================
local job = ws.jobs[0]
dfhack.job.removeJob(job)

-- =============================================================================
-- WORKSHOP TYPES (df.workshop_type)
-- =============================================================================
-- 0: Carpenters     2: Masons        15: Still
-- 3: Craftsdwarfs   5: MetalsmithsForge   19: Kitchen

-- =============================================================================
-- KEY JOB TYPES
-- =============================================================================
-- 69: ConstructBed    70: ConstructThrone   72: ConstructTable
-- 113: BrewDrink      125: MakeBarrel       67: ConstructDoor
