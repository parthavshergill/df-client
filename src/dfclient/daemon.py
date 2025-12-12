"""Persistent daemon for fast DFHack queries.

Keeps a single TCP connection to DFHack open and accepts JSON commands
via a socket on localhost:5001.

Protocol:
- Request: One JSON object per line
- Response: One JSON object per line

Commands:
- {"cmd": "snapshot"}           - Full game state
- {"cmd": "pause"}              - Pause game
- {"cmd": "unpause"}            - Unpause game
- {"cmd": "play", "seconds": N} - Run game for N seconds
- {"cmd": "run", "command": X}  - Run DFHack console command
- {"cmd": "quit"}               - Shutdown daemon
"""

import json
import socket
import time
from typing import Any

from dfclient.client import DFClient


DAEMON_PORT = 5001


class DFDaemon:
    """Daemon that keeps DFHack connection open for fast queries."""

    def __init__(self, port: int = DAEMON_PORT):
        self.port = port
        self.client: DFClient | None = None
        self.server: socket.socket | None = None
        self.running = False

    def connect_dfhack(self) -> bool:
        """Connect to DFHack."""
        try:
            self.client = DFClient()
            status = self.client.connect()
            return status.connected
        except Exception as e:
            print(f"Failed to connect to DFHack: {e}")
            return False

    def _get_state(self, radius: int = 100) -> dict[str, Any]:
        """Get camera-centered game state via Lua.

        Only returns entities within `radius` tiles of camera on same Z-level.
        """
        lua = f'''
local cam_x = df.global.window_x
local cam_y = df.global.window_y
local cam_z = df.global.window_z
local radius = {radius}

print("CAMERA:"..cam_x..","..cam_y..","..cam_z.."|radius="..radius)

local year = df.global.cur_year
local season = ({{"spring","summer","autumn","winter"}})[math.floor(df.global.cur_year_tick/100800)+1] or "?"
print("YEAR:"..year.."/"..season)

-- Helper: check if position is within view
local function inView(x, y, z)
  if z ~= cam_z then return false end
  return math.abs(x - cam_x) <= radius and math.abs(y - cam_y) <= radius
end

-- Dwarves in view with comprehensive status
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) and dfhack.units.isAlive(u) and inView(u.pos.x, u.pos.y, u.pos.z) then
    local name = dfhack.units.getReadableName(u)
    local job = u.job.current_job and df.job_type[u.job.current_job.job_type] or "idle"
    local stress = dfhack.units.getStressCategory(u)
    local pos = u.pos.x..","..u.pos.y

    -- Physical state
    local wounds = #u.body.wounds
    local blood = math.floor(u.body.blood_count * 100 / math.max(1, u.body.blood_max))
    local hunger = u.counters2.hunger_timer < 75000 and "hungry" or nil
    local thirst = u.counters2.thirst_timer < 75000 and "thirsty" or nil
    local tired = u.counters2.sleepiness_timer < 50000 and "tired" or nil

    local phys = {{}}
    if wounds > 0 then table.insert(phys, wounds.." wounds") end
    if blood < 80 then table.insert(phys, blood.."%% blood") end
    if hunger then table.insert(phys, hunger) end
    if thirst then table.insert(phys, thirst) end
    if tired then table.insert(phys, tired) end
    local physStr = #phys > 0 and table.concat(phys, ",") or "healthy"

    -- Top unmet need
    local topNeed = nil
    local worstFocus = 0
    local soul = u.status.current_soul
    if soul then
      for j=0,#soul.personality.needs-1 do
        local n = soul.personality.needs[j]
        if n.focus_level < worstFocus then
          worstFocus = n.focus_level
          topNeed = df.need_type[n.id]
        end
      end
    end

    -- Recent emotion
    local emotion = nil
    if soul and #soul.personality.emotions > 0 then
      local em = soul.personality.emotions[#soul.personality.emotions-1]
      emotion = df.emotion_type[em.type]
    end

    -- Top skill
    local topSkill = nil
    local topLevel = 0
    if soul then
      for j=0,#soul.skills-1 do
        local sk = soul.skills[j]
        if sk.rating > topLevel then
          topLevel = sk.rating
          topSkill = df.job_skill[sk.id]
        end
      end
    end

    local parts = {{pos, name, job, "stress:"..stress, physStr}}
    if topNeed then table.insert(parts, "needs:"..topNeed) end
    if emotion then table.insert(parts, "feeling:"..emotion) end
    if topSkill then table.insert(parts, "best:"..topSkill.."("..topLevel..")") end

    print("DWARF:"..table.concat(parts, "|"))
  end
end

-- Other creatures in view (non-citizen, non-invader)
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isAlive(u) and not dfhack.units.isCitizen(u)
     and not u.flags1.marauder and not u.flags1.active_invader
     and inView(u.pos.x, u.pos.y, u.pos.z) then
    local race = df.global.world.raws.creatures.all[u.race].creature_id
    local pos = u.pos.x..","..u.pos.y
    local job = u.job.current_job and df.job_type[u.job.current_job.job_type] or "wandering"
    print("CREATURE:"..pos.."|"..race.."|"..job)
  end
end

-- Threats in view
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isAlive(u) and (u.flags1.marauder or u.flags1.active_invader)
     and inView(u.pos.x, u.pos.y, u.pos.z) then
    local race = df.global.world.raws.creatures.all[u.race].creature_id
    local pos = u.pos.x..","..u.pos.y
    print("THREAT:"..pos.."|"..race)
  end
end

-- Buildings in view
for i,b in ipairs(df.global.world.buildings.all) do
  if inView(b.centerx, b.centery, b.z) then
    local btype = df.building_type[b:getType()]
    local pos = b.centerx..","..b.centery
    local custom = ""
    if b:getType() == df.building_type.Workshop then
      custom = df.workshop_type[b:getSubtype()] or ""
    elseif b:getType() == df.building_type.Furnace then
      custom = df.furnace_type[b:getSubtype()] or ""
    elseif b:getType() == df.building_type.Stockpile then
      custom = "id="..b.id
    end
    print("BUILDING:"..pos.."|"..btype.."|"..custom)
  end
end

-- Items on ground in view (limit to avoid spam)
local itemCount = 0
for i,item in ipairs(df.global.world.items.all) do
  if itemCount >= 50 then break end
  if item.flags.on_ground and inView(item.pos.x, item.pos.y, item.pos.z) then
    local itype = df.item_type[item:getType()]
    local pos = item.pos.x..","..item.pos.y
    local mat = dfhack.matinfo.decode(item)
    local matName = mat and mat:toString() or ""
    print("ITEM:"..pos.."|"..itype.."|"..matName)
    itemCount = itemCount + 1
  end
end
if itemCount >= 50 then print("ITEM:...|more items truncated") end

-- Terrain sample (check key features in grid)
local terrain = {{walls=0, floors=0, stairs=0, water=0, trees=0}}
local step = math.max(1, math.floor(radius / 10))
for dx = -radius, radius, step do
  for dy = -radius, radius, step do
    local x, y, z = cam_x + dx, cam_y + dy, cam_z
    local tt = dfhack.maps.getTileType(x, y, z)
    if tt then
      local shape = df.tiletype.attrs[tt].shape
      if shape == df.tiletype_shape.WALL then terrain.walls = terrain.walls + 1
      elseif shape == df.tiletype_shape.FLOOR then terrain.floors = terrain.floors + 1
      elseif shape == df.tiletype_shape.STAIR_UP or shape == df.tiletype_shape.STAIR_DOWN
             or shape == df.tiletype_shape.STAIR_UPDOWN then terrain.stairs = terrain.stairs + 1
      end
      local mat = df.tiletype.attrs[tt].material
      if mat == df.tiletype_material.POOL or mat == df.tiletype_material.RIVER then
        terrain.water = terrain.water + 1
      elseif mat == df.tiletype_material.TREE then
        terrain.trees = terrain.trees + 1
      end
    end
  end
end
print("TERRAIN:walls="..terrain.walls.."|floors="..terrain.floors.."|stairs="..terrain.stairs.."|water="..terrain.water.."|trees="..terrain.trees)

-- Active jobs in view
local jobCount = 0
for i,j in ipairs(df.global.world.jobs.list) do
  if jobCount >= 20 then break end
  if j and inView(j.pos.x, j.pos.y, j.pos.z) then
    local jtype = df.job_type[j.job_type]
    local pos = j.pos.x..","..j.pos.y
    local worker = j.holder and dfhack.units.getReadableName(j.holder) or "unassigned"
    print("JOB:"..pos.."|"..jtype.."|"..worker)
    jobCount = jobCount + 1
  end
end

-- Recent announcements (keep global - important alerts)
local ann = df.global.world.status.announcements
local anns = {{}}
for i=#ann-1,math.max(0,#ann-5),-1 do table.insert(anns, ann[i].text) end
if #anns > 0 then print("RECENT:"..table.concat(anns, ";")) end
'''
        result = self.client.run_command(f"lua {lua}", timeout=5.0)

        data = {
            "camera": "",
            "year": "",
            "dwarves": [],
            "creatures": [],
            "threats": [],
            "buildings": [],
            "items": [],
            "terrain": "",
            "jobs": [],
            "recent": []
        }
        for line in result:
            if line.startswith("CAMERA:"):
                data["camera"] = line[7:]
            elif line.startswith("YEAR:"):
                data["year"] = line[5:]
            elif line.startswith("DWARF:"):
                data["dwarves"].append(line[6:])
            elif line.startswith("CREATURE:"):
                data["creatures"].append(line[9:])
            elif line.startswith("THREAT:"):
                data["threats"].append(line[7:])
            elif line.startswith("BUILDING:"):
                data["buildings"].append(line[9:])
            elif line.startswith("ITEM:"):
                data["items"].append(line[5:])
            elif line.startswith("TERRAIN:"):
                data["terrain"] = line[8:]
            elif line.startswith("JOB:"):
                data["jobs"].append(line[4:])
            elif line.startswith("RECENT:"):
                raw = line[7:]
                if raw:
                    data["recent"] = raw.split(";")

        hint = "Use Lua to dig, build, assign labors, or investigate further."
        if data["threats"]:
            hint = "THREATS IN VIEW! Use exterminate or military. " + hint

        data["hint"] = hint
        return data

    def cmd_pause(self) -> dict[str, Any]:
        """Pause the game."""
        if not self.client:
            return {"error": "Not connected"}
        try:
            self.client.pause()
            return {"paused": True}
        except Exception as e:
            return {"error": str(e)}

    def cmd_unpause(self) -> dict[str, Any]:
        """Unpause the game."""
        if not self.client:
            return {"error": "Not connected"}
        try:
            self.client.unpause()
            return {"paused": False}
        except Exception as e:
            return {"error": str(e)}

    def cmd_play(self, seconds: int) -> dict[str, Any]:
        """Run game for N seconds, return state after."""
        if not self.client:
            return {"error": "Not connected"}

        try:
            self.client.unpause()
            time.sleep(seconds)
            self.client.pause()
            state = self._get_state()
            state["seconds"] = seconds
            return state
        except Exception as e:
            return {"error": str(e)}

    def cmd_tick(self, ticks: int) -> dict[str, Any]:
        """Advance game by N ticks (faster than play, uses polling).

        With timestream enabled, this is much faster than real-time waiting.
        """
        if not self.client:
            return {"error": "Not connected"}

        try:
            # Get current tick
            result = self.client.run_command("lua print(df.global.cur_year_tick)", timeout=1.0)
            start_tick = int(result[0]) if result else 0
            target_tick = start_tick + ticks

            self.client.unpause()

            # Poll for tick advancement (check every 50ms)
            max_iterations = ticks * 10  # Safety limit
            iterations = 0
            while iterations < max_iterations:
                time.sleep(0.05)
                result = self.client.run_command("lua print(df.global.cur_year_tick)", timeout=1.0)
                current_tick = int(result[0]) if result else 0
                if current_tick >= target_tick:
                    break
                iterations += 1

            self.client.pause()
            state = self._get_state()
            state["ticks_advanced"] = current_tick - start_tick
            return state
        except Exception as e:
            return {"error": str(e)}

    def cmd_run(self, command: str) -> dict[str, Any]:
        """Run a DFHack console command."""
        if not self.client:
            return {"error": "Not connected"}
        try:
            result = self.client.run_command(command, timeout=5.0)
            return {"output": result}
        except Exception as e:
            return {"error": str(e)}

    def cmd_dig(self, x1: int, y1: int, z1: int, x2: int, y2: int, dig_type: str) -> dict[str, Any]:
        """Designate area for digging."""
        if not self.client:
            return {"error": "Not connected"}

        # Map dig type names to Lua values
        dig_types = {
            "mine": 1,
            "stair_updown": 2,
            "channel": 3,
            "ramp": 4,
            "stair_down": 5,
            "stair_up": 6,
        }
        dig_val = dig_types.get(dig_type, 1)

        lua = f'''
local count = 0
local min_x, max_x = math.min({x1}, {x2}), math.max({x1}, {x2})
local min_y, max_y = math.min({y1}, {y2}), math.max({y1}, {y2})
local z = {z1}
for x = min_x, max_x do
  for y = min_y, max_y do
    local block = dfhack.maps.getTileBlock(x, y, z)
    if block then
      local bx, by = x % 16, y % 16
      local tt = dfhack.maps.getTileType(x, y, z)
      if tt then
        local shape = df.tiletype.attrs[tt].shape
        if shape == df.tiletype_shape.WALL or shape == df.tiletype_shape.FLOOR then
          block.designation[bx][by].dig = {dig_val}
          count = count + 1
        end
      end
    end
  end
end
print("DESIGNATED:"..count)
'''
        try:
            result = self.client.run_command(f"lua {lua}", timeout=3.0)
            count = 0
            for line in result:
                if line.startswith("DESIGNATED:"):
                    count = int(line[11:])
            return {"designated": count, "type": dig_type, "area": f"({x1},{y1},{z1}) to ({x2},{y2},{z1})"}
        except Exception as e:
            return {"error": str(e)}

    def cmd_dig_now(self) -> dict[str, Any]:
        """Instantly complete all dig designations."""
        if not self.client:
            return {"error": "Not connected"}
        try:
            result = self.client.run_command("dig-now", timeout=10.0)
            return {"completed": True, "output": result}
        except Exception as e:
            return {"error": str(e)}

    def cmd_build(self, build_type: str, x: int, y: int, z: int) -> dict[str, Any]:
        """Build workshop/furnace at position."""
        if not self.client:
            return {"error": "Not connected"}

        # Map build type names to workshop subtypes
        workshop_types = {
            "carpenter": 0, "farmer": 1, "mason": 2, "craftsdwarf": 3, "jeweler": 4,
            "metalsmith": 5, "magma_forge": 6, "bowyer": 7, "mechanic": 8, "siege": 9,
            "butcher": 10, "leather": 11, "tanner": 12, "clothier": 13, "fishery": 14,
            "still": 15, "loom": 16, "quern": 17, "kennel": 18, "kitchen": 19,
            "ashery": 20, "dyer": 21, "millstone": 22, "tool": 24,
        }
        furnace_types = {
            "furnace_smelter": 0, "furnace_wood": 1, "furnace_glass": 2, "furnace_kiln": 3,
        }

        if build_type in workshop_types:
            subtype = workshop_types[build_type]
            bld_type = "Workshop"
        elif build_type in furnace_types:
            subtype = furnace_types[build_type]
            bld_type = "Furnace"
        else:
            return {"error": f"Unknown building type: {build_type}"}

        lua = f'''
local pos = df.coord:new()
pos.x, pos.y, pos.z = {x}, {y}, {z}
local bld, err = dfhack.buildings.constructBuilding{{
  type = df.building_type.{bld_type},
  subtype = {subtype},
  custom = -1,
  pos = pos,
  width = 3,
  height = 3
}}
if bld then
  dfhack.buildings.completeBuild(bld)
  print("BUILT:"..bld.id)
else
  print("ERROR:"..(err or "unknown"))
end
'''
        try:
            result = self.client.run_command(f"lua {lua}", timeout=3.0)
            for line in result:
                if line.startswith("BUILT:"):
                    return {"built": build_type, "id": int(line[6:]), "pos": f"({x},{y},{z})"}
                elif line.startswith("ERROR:"):
                    return {"error": line[6:]}
            return {"error": "Unknown result"}
        except Exception as e:
            return {"error": str(e)}

    def cmd_stockpile(self, x: int, y: int, z: int, width: int, height: int, preset: str) -> dict[str, Any]:
        """Create and configure a stockpile."""
        if not self.client:
            return {"error": "Not connected"}

        # Map preset names to library paths
        preset_map = {
            "all": "all", "food": "cat_food", "booze": "booze", "seeds": "seeds",
            "stone": "cat_stone", "wood": "cat_wood", "weapons": "cat_weapons",
            "armor": "cat_armor", "ammo": "cat_ammo", "furniture": "cat_furniture",
            "bars": "cat_bars_blocks", "gems": "cat_gems", "cloth": "cat_cloth",
            "leather": "cat_leather", "finished_goods": "cat_finished_goods",
            "refuse": "cat_refuse", "corpses": "cat_corpses", "animals": "cat_animals",
            "coins": "cat_coins",
        }
        lib_preset = preset_map.get(preset, preset)

        # Step 1: Create stockpile
        lua = f'''
local sp, err = dfhack.buildings.constructBuilding{{
  type = df.building_type.Stockpile,
  pos = {{x={x}, y={y}, z={z}}},
  width = {width},
  height = {height},
  abstract = true
}}
if sp then
  dfhack.buildings.completeBuild(sp)
  print("STOCKPILE:"..sp.id)
else
  print("ERROR:"..(err or "unknown"))
end
'''
        try:
            result = self.client.run_command(f"lua {lua}", timeout=3.0)
            sp_id = None
            for line in result:
                if line.startswith("STOCKPILE:"):
                    sp_id = int(line[10:])
                elif line.startswith("ERROR:"):
                    return {"error": line[6:]}

            if sp_id is None:
                return {"error": "Failed to create stockpile"}

            # Step 2: Configure with preset
            config_result = self.client.run_command(f"stockpiles import library/{lib_preset} -s {sp_id}", timeout=3.0)
            return {"created": True, "id": sp_id, "preset": preset, "pos": f"({x},{y},{z})", "size": f"{width}x{height}"}
        except Exception as e:
            return {"error": str(e)}

    def cmd_order(self, job_type: str, amount: int) -> dict[str, Any]:
        """Create a manager work order."""
        if not self.client:
            return {"error": "Not connected"}

        # Common reactions that need CustomReaction wrapper
        reactions = {
            "brew": "BREW_DRINK_FROM_PLANT",
            "brew_fruit": "BREW_DRINK_FROM_PLANT_GROWTH",
        }

        # Common job types that work directly
        direct_jobs = {
            "MakeCharcoal", "MakeBed", "MakeBarrel", "MakeBin", "MakeTable",
            "MakeChair", "MakeDoor", "MakeCabinet", "MakeBox", "PrepareMeal",
            "ProcessPlants", "MillPlants", "MakeCheese", "TanHide",
        }

        try:
            if job_type.lower() in reactions:
                # Use reaction syntax
                reaction_code = reactions[job_type.lower()]
                json_str = f'{{"job":"CustomReaction","reaction":"{reaction_code}","amount":{amount}}}'
                result = self.client.run_command(f"workorder '{json_str}'", timeout=3.0)
            else:
                # Try direct job type with JSON
                json_str = f'{{"job":"{job_type}","amount":{amount}}}'
                result = self.client.run_command(f"workorder '{json_str}'", timeout=3.0)

            return {"ordered": job_type, "amount": amount, "output": result}
        except Exception as e:
            return {"error": str(e)}

    def cmd_labor(self, name: str, labor: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable labor for a dwarf."""
        if not self.client:
            return {"error": "Not connected"}

        action = "true" if enabled else "false"
        lua = f'''
local found = false
for i, u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) then
    local uname = dfhack.units.getReadableName(u)
    if uname:lower():find("{name.lower()}") then
      local labor_id = df.unit_labor.{labor}
      if labor_id then
        u.status.labors[labor_id] = {action}
        print("SET:"..uname.."|".."{labor}".."|"..tostring({action}))
        found = true
        break
      else
        print("ERROR:Unknown labor {labor}")
        break
      end
    end
  end
end
if not found then print("ERROR:Dwarf not found: {name}") end
'''
        try:
            result = self.client.run_command(f"lua {lua}", timeout=3.0)
            for line in result:
                if line.startswith("SET:"):
                    parts = line[4:].split("|")
                    return {"dwarf": parts[0], "labor": parts[1], "enabled": parts[2] == "true"}
                elif line.startswith("ERROR:"):
                    return {"error": line[6:]}
            return {"error": "Unknown result"}
        except Exception as e:
            return {"error": str(e)}

    def handle_request(self, request: dict) -> dict[str, Any]:
        """Handle a JSON request and return response."""
        start = time.time()
        cmd = request.get("cmd", "")

        if cmd == "snapshot":
            radius = request.get("radius", 100)
            data = self._get_state(radius=int(radius))
        elif cmd == "pause":
            data = self.cmd_pause()
        elif cmd == "unpause":
            data = self.cmd_unpause()
        elif cmd == "play":
            seconds = request.get("seconds", 5)
            data = self.cmd_play(int(seconds))
        elif cmd == "tick":
            ticks = request.get("ticks", 100)
            data = self.cmd_tick(int(ticks))
        elif cmd == "run":
            command = request.get("command", "")
            data = self.cmd_run(command)
        elif cmd == "quit":
            self.running = False
            data = {"shutdown": True}
        # Designation commands
        elif cmd == "dig":
            data = self.cmd_dig(
                request.get("x1", 0), request.get("y1", 0), request.get("z1", 0),
                request.get("x2", 0), request.get("y2", 0), request.get("type", "mine")
            )
        elif cmd == "dig-now":
            data = self.cmd_dig_now()
        elif cmd == "build":
            data = self.cmd_build(
                request.get("type", ""), request.get("x", 0),
                request.get("y", 0), request.get("z", 0)
            )
        elif cmd == "stockpile":
            data = self.cmd_stockpile(
                request.get("x", 0), request.get("y", 0), request.get("z", 0),
                request.get("width", 5), request.get("height", 5), request.get("preset", "all")
            )
        elif cmd == "order":
            data = self.cmd_order(request.get("job", ""), request.get("amount", 1))
        elif cmd == "labor":
            data = self.cmd_labor(
                request.get("name", ""), request.get("labor", ""),
                request.get("enabled", True)
            )
        else:
            data = {"error": f"Unknown command: {cmd}"}

        ms = int((time.time() - start) * 1000)

        if "error" in data:
            return {"ok": False, "error": data["error"], "ms": ms}
        return {"ok": True, "data": data, "ms": ms}

    def handle_client(self, conn: socket.socket) -> None:
        """Handle a single client connection."""
        try:
            # Read until newline
            data = b""
            while b"\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                data += chunk

            line = data.split(b"\n")[0].decode("utf-8")
            request = json.loads(line)

            response = self.handle_request(request)
            conn.sendall(json.dumps(response).encode("utf-8") + b"\n")
        except json.JSONDecodeError as e:
            error = {"ok": False, "error": f"Invalid JSON: {e}"}
            conn.sendall(json.dumps(error).encode("utf-8") + b"\n")
        except Exception as e:
            error = {"ok": False, "error": str(e)}
            conn.sendall(json.dumps(error).encode("utf-8") + b"\n")
        finally:
            conn.close()

    def run(self) -> None:
        """Start the daemon server."""
        if not self.connect_dfhack():
            print("Could not connect to DFHack. Is the game running?")
            return

        print(f"Connected to DFHack")

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", self.port))
        self.server.listen(5)
        self.server.settimeout(1.0)  # Allow checking self.running

        print(f"Daemon listening on localhost:{self.port}")
        print("Commands: snapshot, pause, unpause, play, run, quit")

        self.running = True
        while self.running:
            try:
                conn, addr = self.server.accept()
                self.handle_client(conn)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print("\nShutting down...")
                break

        self.server.close()
        if self.client:
            self.client.disconnect()
        print("Daemon stopped")


def main():
    daemon = DFDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
