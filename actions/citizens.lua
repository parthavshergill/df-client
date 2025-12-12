-- Query citizen data
-- Run via: q.py run "lua <paste code>"

-- List all citizens with names
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then
    print(dfhack.units.getReadableName(u))
  end
end

-- Citizen details (name, profession, stress, job)
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then
    local name = dfhack.units.getReadableName(u)
    local prof = dfhack.units.getProfessionName(u)
    local stress = dfhack.units.getStressCategory(u)
    local job = u.job.current_job and df.job_type[u.job.current_job.job_type] or "idle"
    print(name .. " | " .. prof .. " | stress:" .. stress .. " | " .. job)
  end
end

-- Skills for a citizen (replace ID)
local u = df.unit.find(12345)
if u and u.status.current_soul then
  for i,s in ipairs(u.status.current_soul.skills) do
    if s.rating > 0 then
      print(df.job_skill[s.id] .. ": " .. s.rating)
    end
  end
end

-- Unmet needs for a citizen
local u = df.unit.find(12345)
if u and u.status.current_soul then
  for i,n in ipairs(u.status.current_soul.personality.needs) do
    if n.focus_level < 0 then
      print(df.need_type[n.id] .. ": " .. n.focus_level)
    end
  end
end

-- Current emotions
local u = df.unit.find(12345)
if u and u.status.current_soul then
  for i,e in ipairs(u.status.current_soul.personality.emotions) do
    print(df.emotion_type[e.type] .. " strength:" .. e.strength)
  end
end
