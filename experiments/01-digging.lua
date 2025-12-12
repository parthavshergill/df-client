-- experiments/01-digging.lua
-- Status: working
-- Last tested: 2024-12-12

-- =============================================================================
-- PATTERN: Designate tile for digging
-- =============================================================================
-- dig values: 1=mine, 2=ud-stair, 3=channel, 5=d-stair, 6=u-stair
local x, y, z = 92, 92, 176
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.designation[bx][by].dig = 1  -- 1=mine
block.flags.designated = true
-- Use dig-now to instantly complete

-- =============================================================================
-- DIG DESIGNATION VALUES
-- =============================================================================
-- 1: Mine      → StoneFloor
-- 2: UD-Stair  → StoneStairUD
-- 3: Channel   → RampTop
-- 5: D-Stair   → StoneStairD
-- 6: U-Stair   → StoneStairU (on existing floor)

-- =============================================================================
-- PATTERN: Change tile type directly (existing tiles)
-- =============================================================================
-- Use when dig designation doesn't work (e.g., floor to stair)
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.tiletype[bx][by] = df.tiletype.ConstructedStairU

-- =============================================================================
-- PATTERN: Dig area (multiple tiles)
-- =============================================================================
for dx = 0, 4 do
  for dy = 0, 4 do
    local block = dfhack.maps.getTileBlock(x + dx, y + dy, z)
    local bx, by = (x + dx) % 16, (y + dy) % 16
    block.designation[bx][by].dig = 1
    block.flags.designated = true
  end
end

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Smooth/engrave designations
-- [ ] Ramp digging
-- [ ] Clear designation (dig = 0)
