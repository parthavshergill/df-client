-- experiments/11-orchestration.lua
-- Status: working
-- Last tested: 2024-12-12
-- Patterns for orchestrating dwarves (jobs, labors, needs)

-- =============================================================================
-- CRITICAL: Triggering Game Engine (the key insight!)
-- =============================================================================
-- Direct data structure modification (e.g., block.designation[bx][by].dig = 1)
-- does NOT trigger game engine logic. You MUST call these functions:

-- After setting designations:
dfhack.job.checkDesignationsNow()  -- Creates jobs from designations AND assigns workers

-- To manually assign a worker to a job:
dfhack.job.addWorker(job, unit)    -- Forces unit to work on job

-- To trigger building job checks:
dfhack.job.checkBuildingsNow()     -- Creates jobs for buildings needing work

-- =============================================================================
-- PATTERN: Enable labor for all dwarves
-- =============================================================================
for _, u in ipairs(dfhack.units.getCitizens()) do
  u.status.labors[df.unit_labor.MINE] = true
  u.status.labors[df.unit_labor.HAUL_FOOD] = true
  u.status.labors[df.unit_labor.BREWER] = true
end

-- =============================================================================
-- PATTERN: Check dwarf needs
-- =============================================================================
for _, u in ipairs(dfhack.units.getCitizens()) do
  print(u.name.first_name,
    'hunger:', u.counters2.hunger_timer,
    'thirst:', u.counters2.thirst_timer,
    'sleep:', u.counters2.sleepiness_timer)
end
-- Hungry ~3000-5000, Starving ~20000+

-- =============================================================================
-- PATTERN: Reset dwarf needs (cheat)
-- =============================================================================
for _, u in ipairs(dfhack.units.getCitizens()) do
  u.counters2.hunger_timer = 0
  u.counters2.thirst_timer = 0
  u.counters2.sleepiness_timer = 0
end
-- Alternative: dfhack.run_script('full-heal', '-all')

-- =============================================================================
-- PATTERN: Assign Eat job to dwarf (manual)
-- =============================================================================
-- Dwarves may not auto-eat. This pattern forces eating.
local u = dfhack.units.getCitizens()[1]
local food = df.item.find(534)  -- food item id
local job = df.job:new()
job.job_type = df.job_type.Eat
job.pos.x = food.pos.x
job.pos.y = food.pos.y
job.pos.z = food.pos.z
local itemref = df.job_item_ref:new()
itemref.item = food
job.items:insert('#', itemref)
food.flags.in_job = true
dfhack.job.linkIntoWorld(job)
local jref = df.general_ref_unit_workerst:new()
jref.unit_id = u.id
job.general_refs:insert('#', jref)
u.job.current_job = job

-- =============================================================================
-- PATTERN: Free item from container
-- =============================================================================
-- Items in containers have pos = -30000,-30000,-30000
local item = df.item.find(527)
for i=#item.general_refs-1,0,-1 do
  local ref = item.general_refs[i]
  if df.general_ref_contained_in_itemst:is_instance(ref) then
    item.general_refs:erase(i)
  end
end
item.pos.x = 94  -- set actual position
item.pos.y = 94
item.pos.z = 178
item.flags.in_inventory = false

-- =============================================================================
-- PATTERN: Check current job
-- =============================================================================
for _, u in ipairs(dfhack.units.getCitizens()) do
  local j = u.job.current_job
  if j then
    print(u.name.first_name, df.job_type[j.job_type], 'timer:', j.completion_timer)
  else
    print(u.name.first_name, 'idle')
  end
end

-- =============================================================================
-- PATTERN: Cancel dwarf's current job
-- =============================================================================
local u = dfhack.units.getCitizens()[1]
if u.job.current_job then
  dfhack.job.removeJob(u.job.current_job)
end

-- =============================================================================
-- JOB TYPES (automatic dwarf actions)
-- =============================================================================
-- 17: Eat           19: Drink         23: Sleep
-- 50: Rest          66: ConstructBuilding

-- =============================================================================
-- LABOR TYPES (df.unit_labor)
-- =============================================================================
-- MINE, HAUL_FOOD, HAUL_ITEM, BREWER, PLANT, CARPENTRY, MASONRY, STONECRAFT

-- =============================================================================
-- OBSERVATIONS
-- =============================================================================
-- - Workshop jobs (brewing, carpentry) are picked up quickly by idle dwarves
-- - Dwarves need pickaxes to mine (3 picks available from embark)
-- - Hauling jobs may require stockpile zones to trigger
-- - Dwarves DO eat when given Eat jobs with proper item references
-- - Food in containers (pos -30000,-30000,-30000) may not be accessible
-- - full-heal -all resets all needs (hunger, thirst, sleep) to 0

-- =============================================================================
-- FOOD ACCESSIBILITY
-- =============================================================================
-- - Food/drink inside barrels shows pos = -30000,-30000,-30000
-- - CONFIRMED: Dwarves do NOT auto-eat/drink in this setup
-- - Use full-heal -all to reset needs, or assign Eat jobs manually
-- - Stockpile location doesn't trigger auto-eat behavior

-- =============================================================================
-- STAIR CONNECTIVITY
-- =============================================================================
-- For dwarves to path between z-levels, need proper stair chain:
-- - z+1: ConstructedStairD or StoneStairD (goes DOWN)
-- - z:   StoneStairUD or SoilStairUD (goes UP and DOWN)
-- - z-1: StoneStairU or StoneStairUD (goes UP)
-- To create stairs via dwarf labor:
-- - On WALL tiles: designate dig=2 (UD stair) → Dig job
-- - On FLOOR tiles: designate dig=2 → CarveUpDownStaircase job
-- - On EXISTING STAIRS: CANNOT upgrade (gives "Inappropriate dig square")
-- IMPORTANT: Direct tiletype modification resets during game ticks!

-- =============================================================================
-- KNOWN ISSUES
-- =============================================================================
-- - Dwarves may not auto-assign to dig jobs in certain game states
-- - Stairs reset to D-only can break pathing silently
-- - Workshop jobs (brewing, carpentry) are picked up more reliably
-- - Full-heal workaround needed for eat/drink behavior

-- =============================================================================
-- PATTERN: Proper dig designation workflow
-- =============================================================================
-- This is the CORRECT way to designate digging:
local x, y, z = 95, 93, 175
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.designation[bx][by].dig = 1  -- 1=mine
block.flags.designated = true
dfhack.job.checkDesignationsNow()  -- CRITICAL: creates jobs and assigns workers
-- Now tick and dwarves will dig!

-- =============================================================================
-- PATTERN: Find and manually assign dig job
-- =============================================================================
-- If checkDesignationsNow doesn't assign workers, do it manually:
for _, job in ipairs(df.global.world.jobs.list) do
  if job.job_type == df.job_type.Dig then
    local unit = dfhack.units.getCitizens()[1]
    dfhack.job.addWorker(job, unit)
    break
  end
end

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [x] Test if food in stockpile triggers auto-eat (NO - confirmed)
-- [x] Why dwarves don't auto-assign to dig jobs (SOLVED: need checkDesignationsNow)
-- [ ] Burrow assignment for keeping dwarves together
-- [ ] Drink job pattern (similar to Eat)
