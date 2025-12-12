-- Job creation via Lua
-- Run via: q.py run "lua <code>"

-- Create a job directly (bypasses manager)
local j = dfhack.job.createLinked()
j.job_type = df.job_type.FellTree  -- or other job type
j.pos.x, j.pos.y, j.pos.z = 87, 79, 178

-- Common job types:
-- 5=Dig, 6=CarveUpwardStaircase, 7=CarveDownwardStaircase
-- 10=DigChannel, 11=FellTree, 12=GatherPlants
-- 17=Eat, 19=Drink, 23=Sleep, 25=Fish, 26=Hunt

-- Find a tree and create FellTree job
for i,p in ipairs(df.global.world.plants.all) do
  if p.tree_info and p.pos.z == 178 then
    local j = dfhack.job.createLinked()
    j.job_type = df.job_type.FellTree
    j.pos.x, j.pos.y, j.pos.z = p.pos.x, p.pos.y, p.pos.z
    print("Created FellTree at "..p.pos.x..","..p.pos.y)
    break
  end
end

-- List pending jobs
local utils = require('utils')
for _,j in utils.listpairs(df.global.world.jobs.list) do
  print(df.job_type[j.job_type].." at "..j.pos.x..","..j.pos.y..","..j.pos.z)
end

-- Manager work orders (use DFHack command)
-- q.py run "workorder BrewDrink 10"
-- q.py run "workorder MakeCharcoal"
