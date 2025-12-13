-- Dig designation patterns
-- Run via: q.py run "lua <code>"

-- =============================================================================
-- PROPER DIGGING (dwarves complete the work)
-- =============================================================================
-- Step 1: Set designation
-- Step 2: Call checkDesignationsNow() to create jobs
-- Step 3: Tick and dwarves will dig

local x, y, z = 95, 93, 175
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16

-- Set designation (only works on WALL tiles, not floors!)
-- Use proper enums instead of raw integers:
block.designation[bx][by].dig = df.tile_dig_designation.Default  -- mine wall
block.flags.designated = true

-- CRITICAL: Trigger game engine to create jobs
dfhack.job.checkDesignationsNow()

print("Designated and triggered job creation")

-- =============================================================================
-- DESIGNATE AREA
-- =============================================================================
local x1, y1, z = 90, 90, 175
local x2, y2 = 95, 95

for x = x1, x2 do
  for y = y1, y2 do
    local block = dfhack.maps.getTileBlock(x, y, z)
    local bx, by = x % 16, y % 16
    block.designation[bx][by].dig = df.tile_dig_designation.Default
    block.flags.designated = true
  end
end
dfhack.job.checkDesignationsNow()  -- Create all jobs at once

-- =============================================================================
-- DIG DESIGNATION ENUMS (df.tile_dig_designation)
-- =============================================================================
-- No               = 0 (Clear designation)
-- Default          = 1 (Mine: wall → floor)
-- UpDownStair      = 2 (wall → StairUD)
-- Channel          = 3 (floor → hole + ramp below)
-- Ramp             = 4 (wall → ramp)
-- DownStair        = 5 (wall → StairD)
-- UpStair          = 6 (existing floor → StairU)

-- =============================================================================
-- MANUALLY ASSIGN WORKER TO DIG JOB
-- =============================================================================
-- If checkDesignationsNow doesn't assign workers automatically:
local link = df.global.world.jobs.list.next
while link do
  local j = link.item
  if j and j.job_type == df.job_type.Dig then
    local miner = dfhack.units.getCitizens()[1]  -- first citizen
    dfhack.job.addWorker(j, miner)
    print("Assigned", miner.name.first_name, "to dig job", j.id)
    break
  end
  link = link.next
end

-- =============================================================================
-- INSTANT DIG (cheat)
-- =============================================================================
-- q.py run "dig-now"

-- =============================================================================
-- LIMITATIONS
-- =============================================================================
-- - Can only designate WALL tiles for digging, not floors
-- - CarveUpDownStaircase on existing stairs gives "Inappropriate dig square"
-- - Direct tiletype modification may be reset by game engine
