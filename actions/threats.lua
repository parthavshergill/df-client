-- Query threats/invaders
-- Run via: q.py run "lua <paste code>"

-- List all hostile units
for i,u in ipairs(df.global.world.units.active) do
  if u.flags1.marauder or u.flags1.active_invader or u.flags2.visitor_hostile then
    local race = df.global.world.raws.creatures.all[u.race].creature_id
    print("ID:" .. u.id .. " " .. race)
  end
end

-- Count threats by race
local counts = {}
for i,u in ipairs(df.global.world.units.active) do
  if u.flags1.marauder or u.flags1.active_invader or u.flags2.visitor_hostile then
    local race = df.global.world.raws.creatures.all[u.race].creature_id
    counts[race] = (counts[race] or 0) + 1
  end
end
for race, count in pairs(counts) do
  print(race .. ": " .. count)
end

-- Kill specific race
-- Use: q.py run "exterminate RACE"

-- Kill all hostiles
-- Use: q.py run "exterminate all"
