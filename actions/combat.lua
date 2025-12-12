-- Combat and military actions
-- Run via: q.py run "lua <paste code>" or q.py run "<command>"

-- Kill all of a race
-- q.py run "exterminate MAGMA_CRAB"
-- q.py run "exterminate IMP_FIRE"
-- q.py run "exterminate GOBLIN"

-- Kill all hostiles
-- q.py run "exterminate all"

-- Heal all dwarves
-- q.py run "full-heal -r"

-- Heal specific unit
-- q.py run "full-heal -unit <ID>"

-- Make dwarves combat-hardened (no panic)
-- q.py run "combat-harden -a"

-- Remove bad thoughts
-- q.py run "remove-stress -a"

-- List military squads
for i, squad in ipairs(df.global.world.squads.all) do
  if squad.entity_id == df.global.plotinfo.group_id then
    local name = dfhack.TranslateName(squad.name)
    local count = 0
    for j, pos in ipairs(squad.positions) do
      if pos.occupant ~= -1 then count = count + 1 end
    end
    print("Squad: " .. name .. " (" .. count .. " members)")
  end
end

-- Get squad member names
local squad = df.global.world.squads.all[0]  -- change index
for i, pos in ipairs(squad.positions) do
  if pos.occupant ~= -1 then
    local u = df.unit.find(pos.occupant)
    if u then print(dfhack.units.getReadableName(u)) end
  end
end
