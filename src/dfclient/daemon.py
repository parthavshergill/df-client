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

    def get_snapshot(self) -> dict[str, Any]:
        """Get full game state via Lua queries."""
        if not self.client:
            return {"error": "Not connected to DFHack"}

        try:
            # Single Lua script that outputs all data as key=value pairs
            lua_code = '''
local out = {}
-- Basic info
out.year = df.global.cur_year
out.paused = df.global.pause_state and 1 or 0
out.camera_x = df.global.window_x
out.camera_y = df.global.window_y
out.camera_z = df.global.window_z

-- Count citizens
local citizens = 0
local idle = 0
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isCitizen(u) and dfhack.units.isAlive(u) then
    citizens = citizens + 1
    if not u.job.current_job then idle = idle + 1 end
  end
end
out.citizens = citizens
out.idle = idle

-- Count threats
local threats = 0
for i,u in ipairs(df.global.world.units.active) do
  if dfhack.units.isAlive(u) and (u.flags1.marauder or u.flags1.active_invader) then
    threats = threats + 1
  end
end
out.threats = threats

-- Output as parseable lines
for k,v in pairs(out) do print(k.."="..tostring(v)) end
'''
            result = self.client.run_command(f"lua {lua_code}", timeout=2.0)

            # Parse key=value output
            data = {}
            for line in result:
                if "=" in line:
                    key, val = line.split("=", 1)
                    # Convert to int if possible
                    try:
                        data[key] = int(val)
                    except ValueError:
                        data[key] = val

            return {
                "year": data.get("year", 0),
                "citizens": data.get("citizens", 0),
                "idle": data.get("idle", 0),
                "paused": data.get("paused", 0) == 1,
                "camera": {
                    "x": data.get("camera_x", 0),
                    "y": data.get("camera_y", 0),
                    "z": data.get("camera_z", 0),
                },
                "threats": data.get("threats", 0),
            }
        except Exception as e:
            return {"error": str(e)}

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
        """Run game for N seconds and return changes."""
        if not self.client:
            return {"error": "Not connected"}

        try:
            before = self.get_snapshot()
            if "error" in before:
                return before

            self.client.unpause()
            time.sleep(seconds)
            self.client.pause()

            after = self.get_snapshot()
            if "error" in after:
                return after

            # Compute changes
            changes = []
            if after["citizens"] < before["citizens"]:
                changes.append(f"LOST {before['citizens'] - after['citizens']} citizen(s)!")
            elif after["citizens"] > before["citizens"]:
                changes.append(f"Gained {after['citizens'] - before['citizens']} citizen(s)")

            if after["threats"] < before["threats"]:
                changes.append(f"Killed {before['threats'] - after['threats']} threat(s)")
            elif after["threats"] > before["threats"]:
                changes.append(f"New threats: +{after['threats'] - before['threats']}")

            return {
                "seconds": seconds,
                "before": before,
                "after": after,
                "changes": changes if changes else ["No significant changes"],
            }
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
            data = self.get_snapshot()
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
