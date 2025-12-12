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
