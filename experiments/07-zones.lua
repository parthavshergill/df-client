-- experiments/07-zones.lua
-- Status: working
-- Last tested: 2024-12-12

-- =============================================================================
-- PATTERN: Create zone (activity zone)
-- =============================================================================
local z = dfhack.buildings.constructBuilding{
  type = df.building_type.Civzone,
  pos = {x=92, y=92, z=178},
  width = 5, height = 5,
  abstract = true
}
-- Returns zone with id

-- =============================================================================
-- PATTERN: Set zone type
-- =============================================================================
-- Zone types: 0=Home, 7=MeadHall, 10=Temple, 19=Library
local z = df.building.find(2)
z.type = 7  -- MeadHall (meeting hall)

-- =============================================================================
-- ZONE TYPES (df.civzone_type)
-- =============================================================================
-- 0: Home           7: MeadHall      10: Temple
-- 1: Depot          8: ThroneRoom    11: Kitchen
-- 2: Stockpile      15: Treasury     19: Library
-- 3: NobleQuarters  16: GuardPost    20: Plot

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Bedroom assignment (from bed)
-- [ ] Hospital zone
-- [ ] Garbage dump zone
-- [ ] Pen/pasture for animals
