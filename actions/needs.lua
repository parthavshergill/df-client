-- Dwarf needs and physical state
-- Run via: q.py run "lua <code>"

-- Check a dwarf's needs
local u = df.global.world.units.active[0]
print("hunger_timer: "..u.counters2.hunger_timer)  -- 0 = starving
print("thirst_timer: "..u.counters2.thirst_timer)  -- 0 = dehydrated
print("sleepiness_timer: "..u.counters2.sleepiness_timer)  -- 0 = exhausted

-- Instantly satisfy needs (emergency)
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) and dfhack.units.isAlive(u) then
    u.counters2.hunger_timer = 100000
    u.counters2.thirst_timer = 100000
    u.counters2.sleepiness_timer = 100000
  end
end

-- Check stress and emotions
local soul = u.status.current_soul
if soul then
  local stress = dfhack.units.getStressCategory(u)  -- 0-6 scale
  local emotion = soul.personality.emotions[#soul.personality.emotions-1]
  print("stress: "..stress)
  if emotion then print("emotion: "..df.emotion_type[emotion.type]) end
end

-- Check physical state
print("wounds: "..#u.body.wounds)
print("blood: "..u.body.blood_count.."/"..u.body.blood_max)

-- Resurrect/heal
-- q.py run "full-heal -unit ID -r"
