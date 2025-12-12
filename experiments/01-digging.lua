-- experiments/01-digging.lua
-- Status: untested
-- Patterns for dig designations, stairs, channels, ramps

-- =============================================================================
-- PATTERN: Designate area for mining
-- =============================================================================
-- block.designation[bx][by].dig = 1 (mine), 2 (ud-stair), 3 (channel), 5 (d-stair), 6 (u-stair)

-- =============================================================================
-- PATTERN: Change existing tile type
-- =============================================================================
-- block.tiletype[bx][by] = df.tiletype.ConstructedStairU

-- =============================================================================
-- TODO: Explore
-- =============================================================================
-- [ ] Ramp designations
-- [ ] Smooth/engrave
-- [ ] Remove designation
