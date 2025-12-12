-- Job creation and management patterns
-- Run via: q.py run "lua <code>"

-- =============================================================================
-- CRITICAL: Game Engine Triggering
-- =============================================================================
-- Direct data modification doesn't trigger game logic. Call these after changes:

dfhack.job.checkDesignationsNow()  -- Create jobs from dig/chop designations
dfhack.job.checkBuildingsNow()     -- Create jobs for building construction
dfhack.job.addWorker(job, unit)    -- Manually assign worker to specific job

-- =============================================================================
-- ADD WORKSHOP JOB (with proper material filter)
-- =============================================================================
local ws = df.building.find(4)  -- carpenter workshop ID
local job = df.job:new()
job.job_type = df.job_type.MakeBarrel  -- or integer 125

-- Material filter (REQUIRED for most workshop jobs)
local jitem = df.job_item:new()
jitem.item_type = df.item_type.WOOD
jitem.mat_type = -1
jitem.mat_index = -1
jitem.quantity = 1
jitem.vector_id = df.job_item_vector_id.WOOD
job.job_items.elements:insert('#', jitem)

dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)
print("Added job to workshop", ws.id)

-- =============================================================================
-- LIST JOBS
-- =============================================================================
local link = df.global.world.jobs.list.next
while link do
  local j = link.item
  if j then
    print(j.id, df.job_type[j.job_type], j.pos.x..','..j.pos.y..','..j.pos.z)
  end
  link = link.next
end

-- =============================================================================
-- FIND JOB BY TYPE AND ASSIGN WORKER
-- =============================================================================
local link = df.global.world.jobs.list.next
while link do
  local j = link.item
  if j and j.job_type == df.job_type.Dig then
    local unit = dfhack.units.getCitizens()[1]
    dfhack.job.addWorker(j, unit)
    print("Assigned", unit.name.first_name, "to job", j.id)
    break
  end
  link = link.next
end

-- =============================================================================
-- CANCEL JOB
-- =============================================================================
local job = ...  -- job reference
dfhack.job.removeJob(job)

-- =============================================================================
-- JOB TYPES (common)
-- =============================================================================
-- 69: ConstructBed       70: ConstructThrone (chair)
-- 72: ConstructTable     67: ConstructDoor
-- 113: BrewDrink         125: MakeBarrel
-- 126: MakeBucket        184: MakeCharcoal
