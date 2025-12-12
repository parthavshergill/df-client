-- experiments/06-furniture.lua
-- Status: working
-- Last tested: 2024-12-12

-- =============================================================================
-- PATTERN: Add furniture construction job to carpenter
-- =============================================================================
-- Job types: 69=ConstructBed, 70=ConstructThrone(chair), 72=ConstructTable
-- Requires job_item with vector_id=18 (WOOD)
local ws = df.building.find(4)  -- carpenter workshop id
local job = df.job:new()
job.job_type = 69  -- ConstructBed
local jitem = df.job_item:new()
jitem.item_type = df.item_type.WOOD
jitem.mat_type = -1
jitem.mat_index = -1
jitem.quantity = 1
jitem.vector_id = 18  -- WOOD vector
job.job_items.elements:insert('#', jitem)
dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)

-- =============================================================================
-- PATTERN: Place furniture as building
-- =============================================================================
-- Requires furniture item (bed, table, chair, door)
local bed = df.item.find(1268)  -- bed item id
local bld = dfhack.buildings.constructBuilding{
  type = df.building_type.Bed,  -- or Table, Chair, Door
  pos = {x=93, y=96, z=178},
  items = {bed}
}
dfhack.buildings.completeBuild(bld)
bld.construction_stage = 3
-- Returns building with id

-- =============================================================================
-- FURNITURE JOB TYPES (carpenter)
-- =============================================================================
-- 69: ConstructBed        70: ConstructThrone (chair)
-- 72: ConstructTable      67: ConstructDoor

-- =============================================================================
-- FURNITURE BUILDING TYPES
-- =============================================================================
-- df.building_type.Bed    df.building_type.Table
-- df.building_type.Chair  df.building_type.Door

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Assign bed to dwarf (bedroom)
-- [ ] Assign table/chair as dining room
-- [ ] Check furniture quality
