-- experiments/03-workshops.lua
-- Status: untested
-- Patterns for workshop building and job management

-- =============================================================================
-- PATTERN: Build workshop
-- =============================================================================
-- dfhack.buildings.constructBuilding{type=df.building_type.Workshop, subtype=N, pos={...}}
-- bld.construction_stage = 3 (instant complete)

-- =============================================================================
-- PATTERN: Find workshop by ID
-- =============================================================================
-- df.building.find(ID)

-- =============================================================================
-- PATTERN: Add job to workshop
-- =============================================================================
-- job = df.job:new(); job.job_type = N; dfhack.job.linkIntoWorld(job); dfhack.job.assignToWorkshop(job, ws)

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Find workshop by type/subtype
-- [ ] List jobs in workshop
-- [ ] Cancel job
