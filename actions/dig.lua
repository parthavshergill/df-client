-- Dig designations via Lua
-- Run via: q.py run "lua <code>"

-- Dig types:
-- 0 = No, 1 = Default, 2 = UpDownStair, 3 = Channel, 4 = Ramp, 5 = DownStair, 6 = UpStair

-- Designate single tile for digging
local x, y, z = 40, 78, 177
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16
block.designation[bx][by].dig = 1  -- 1 = normal dig
print("Designated tile for digging")

-- Designate area for digging (e.g., 3x3)
for dx = 0, 2 do
  for dy = 0, 2 do
    local x, y, z = 40 + dx, 78 + dy, 177
    local block = dfhack.maps.getTileBlock(x, y, z)
    local bx, by = x % 16, y % 16
    block.designation[bx][by].dig = 1
  end
end
print("Designated 3x3 area for digging")

-- Designate down stair
block.designation[bx][by].dig = 5

-- Designate up stair
block.designation[bx][by].dig = 6

-- Designate up/down stair
block.designation[bx][by].dig = 2

-- Designate channel
block.designation[bx][by].dig = 3

-- INSTANT DIG: After setting designations, run:
-- q.py run "dig-now"
-- This instantly completes all dig designations on the map

-- Check tile type
print(df.tiletype[dfhack.maps.getTileType(x, y, z)])

-- Check if tile is hidden
local hidden = block.designation[bx][by].hidden
print("Hidden:", hidden)

-- =============================================================================
-- CHANGING EXISTING TILES (when dig designation doesn't work)
-- =============================================================================
-- Dig designations only work on WALLS, not existing floors!
-- To change an existing floor to stairs, modify the tiletype directly:

local x, y, z = 95, 95, 176
local block = dfhack.maps.getTileBlock(x, y, z)
local bx, by = x % 16, y % 16

-- Change floor to up-stair
block.tiletype[bx][by] = df.tiletype.ConstructedStairU

-- Change floor to down-stair
block.tiletype[bx][by] = df.tiletype.ConstructedStairD

-- Change floor to up/down-stair
block.tiletype[bx][by] = df.tiletype.ConstructedStairUD

-- Verify the change
local tt = dfhack.maps.getTileType(x, y, z)
print("New shape:", df.tiletype.attrs[tt].shape)
