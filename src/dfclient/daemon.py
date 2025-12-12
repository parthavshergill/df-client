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

    def _get_state(self) -> dict[str, Any]:
        """Get comprehensive dwarf-focused game state via Lua."""
        lua = '''
local year = df.global.cur_year
local season = ({"spring","summer","autumn","winter"})[math.floor(df.global.cur_year_tick/100800)+1] or "?"
print("YEAR:"..year.."/"..season)

-- Dwarves with comprehensive status
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) and dfhack.units.isAlive(u) then
    local name = dfhack.units.getReadableName(u)
    local job = u.job.current_job and df.job_type[u.job.current_job.job_type] or "idle"
    local stress = dfhack.units.getStressCategory(u)

    -- Physical state
    local wounds = #u.body.wounds
    local blood = math.floor(u.body.blood_count * 100 / math.max(1, u.body.blood_max))
    local hunger = u.counters2.hunger_timer < 75000 and "hungry" or nil
    local thirst = u.counters2.thirst_timer < 75000 and "thirsty" or nil
    local tired = u.counters2.sleepiness_timer < 50000 and "tired" or nil

    local phys = {}
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

    local parts = {name, job, "stress:"..stress, physStr}
    if topNeed then table.insert(parts, "needs:"..topNeed) end
    if emotion then table.insert(parts, "feeling:"..emotion) end
    if topSkill then table.insert(parts, "best:"..topSkill.."("..topLevel..")") end

    print("DWARF:"..table.concat(parts, "|"))
  end
end

-- Threats
local threats = {}
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isAlive(u) and (u.flags1.marauder or u.flags1.active_invader) then
    local race = df.global.world.raws.creatures.all[u.race].creature_id
    table.insert(threats, race.."@"..u.pos.x..","..u.pos.y..","..u.pos.z)
  end
end
if #threats > 0 then print("THREATS:"..table.concat(threats, ";")) end

-- Recent announcements
local ann = df.global.world.status.announcements
local anns = {}
for i=#ann-1,math.max(0,#ann-3),-1 do table.insert(anns, ann[i].text) end
if #anns > 0 then print("RECENT:"..table.concat(anns, ";")) end
'''
        result = self.client.run_command(f"lua {lua}", timeout=3.0)

        data = {"year": "", "dwarves": [], "threats": [], "recent": []}
        for line in result:
            if line.startswith("YEAR:"):
                data["year"] = line[5:]
            elif line.startswith("DWARF:"):
                data["dwarves"].append(line[6:])
            elif line.startswith("THREATS:"):
                raw = line[8:]
                if raw:
                    data["threats"] = raw.split(";")
            elif line.startswith("RECENT:"):
                raw = line[7:]
                if raw:
                    data["recent"] = raw.split(";")

        hint = "Use Lua to dig, build, assign labors, or investigate further."
        if data["threats"]:
            hint = "THREATS ACTIVE. Use exterminate or military. " + hint

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

    def cmd_run(self, command: str) -> dict[str, Any]:
        """Run a DFHack console command."""
        if not self.client:
            return {"error": "Not connected"}
        try:
            result = self.client.run_command(command, timeout=5.0)
            return {"output": result}
        except Exception as e:
            return {"error": str(e)}

    def handle_request(self, request: dict) -> dict[str, Any]:
        """Handle a JSON request and return response."""
        start = time.time()
        cmd = request.get("cmd", "")

        if cmd == "snapshot":
            data = self._get_state()
        elif cmd == "pause":
            data = self.cmd_pause()
        elif cmd == "unpause":
            data = self.cmd_unpause()
        elif cmd == "play":
            seconds = request.get("seconds", 5)
            data = self.cmd_play(int(seconds))
        elif cmd == "run":
            command = request.get("command", "")
            data = self.cmd_run(command)
        elif cmd == "quit":
            self.running = False
            data = {"shutdown": True}
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
