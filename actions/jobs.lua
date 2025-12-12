-- Job creation via Lua
-- Run via: q.py run "lua <code>"

-- =============================================================================
-- WORKSHOP JOBS (recommended - this pattern works!)
-- =============================================================================
-- Use df.job:new() + linkIntoWorld() + assignToWorkshop()
-- Use INTEGER job types (enum names like df.job_type.BrewDrink may not exist!)

-- Add job to workshop (e.g., brewing at still)
local ws = df.building.find(3)  -- find workshop by ID
local job = df.job:new()
job.job_type = 113  -- ProcessPlantsBarrel = brewing
dfhack.job.linkIntoWorld(job)
dfhack.job.assignToWorkshop(job, ws)
print("Added brewing job to workshop", ws.id)

-- Common workshop job types (use integers!):
-- 113 = ProcessPlantsBarrel (brewing)
-- 125 = MakeBarrel
-- 126 = MakeBucket
-- 82  = MakeCrafts
-- 184 = MakeCharcoal

-- =============================================================================
-- STANDALONE JOBS (less tested - may need additional setup)
-- =============================================================================
-- Jobs like FellTree, Dig, etc. may need item refs set up properly

-- List pending jobs
for _,j in ipairs(df.global.world.jobs.list) do
  if j then
    print(df.job_type[j.job_type].." at "..j.pos.x..","..j.pos.y..","..j.pos.z)
  end
end

-- =============================================================================
-- MANAGER WORK ORDERS - REQUIRES MANAGER NOBLE!
-- =============================================================================
-- WARNING: These commands only work if you have a manager assigned!
-- For early game, use direct job creation above instead.
--
-- q.py run "workorder BrewDrink 10"
-- q.py run "workorder MakeCharcoal"
