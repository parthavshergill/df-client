-- Query world/fortress state
-- Run via: q.py run "lua <paste code>"

-- Year and season
local year = df.global.cur_year
local tick = df.global.cur_year_tick
local season_names = {"spring", "summer", "autumn", "winter"}
local season = season_names[math.floor(tick / 100800) + 1] or "unknown"
print("Year " .. year .. ", " .. season)

-- Fortress name (if embark exists)
local site = df.global.world.world_data.active_site[0]
if site then
  print("Site: " .. dfhack.TranslateName(site.name))
end

-- Recent announcements (last 10)
local ann = df.global.world.status.announcements
for i = #ann - 1, math.max(0, #ann - 10), -1 do
  print(ann[i].text)
end

-- Recent combat reports
local rep = df.global.world.status.reports
for i = #rep - 1, math.max(0, #rep - 10), -1 do
  print(rep[i].text)
end

-- Weather
print("Rain: " .. tostring(df.global.cur_rain > 0))
print("Snow: " .. tostring(df.global.cur_snow > 0))

-- Camera position
local vp = df.global.window_x
print("Camera: " .. df.global.window_x .. "," .. df.global.window_y .. "," .. df.global.window_z)

-- Population count
local citizens = 0
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then citizens = citizens + 1 end
end
print("Citizens: " .. citizens)
