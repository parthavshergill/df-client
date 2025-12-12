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

from dfclient.client import DFClient, _parse_protobuf, _get_int, _get_string, _get_profession_name


DAEMON_PORT = 5001


def get_threats(raw_units: list[dict]) -> tuple[list[dict], int]:
    """Extract threat information from raw units."""
    threats = []
    dead_hostiles = 0

    for u in raw_units:
        flags1 = _get_int(u, 8)
        flags2 = _get_int(u, 9)

        is_dead = bool(flags1 & 0x2)
        is_active_invader = bool(flags1 & 0x80000)
        is_hidden_ambusher = bool(flags1 & 0x40000)
        is_invader_origin = bool(flags2 & 0x1)

        if not (is_active_invader or is_hidden_ambusher or is_invader_origin):
            continue

        if is_dead:
            dead_hostiles += 1
            continue

        prof_data = u.get(16)
        prof_id = 0
        if isinstance(prof_data, bytes):
            pf = _parse_protobuf(prof_data)
            prof_id = _get_int(pf, 3)

        threats.append({
            "id": _get_int(u, 1),
            "profession": _get_profession_name(prof_id),
            "x": _get_int(u, 2),
            "y": _get_int(u, 3),
            "z": _get_int(u, 4),
        })

    return threats, dead_hostiles


def get_notable_citizens(raw_units: list[dict], limit: int = 5) -> list[dict]:
    """Get notable citizens (military)."""
    military_profs = {73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83,
                      87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97,
                      98, 99, 100, 101, 102}

    notable = []
    for u in raw_units:
        flags1 = _get_int(u, 8)
        is_dead = bool(flags1 & 0x2)
        if is_dead:
            continue

        civ_data = u.get(6)
        if not isinstance(civ_data, bytes):
            continue
        civ_fields = _parse_protobuf(civ_data)
        civ_id = _get_int(civ_fields, 1, -1)
        if civ_id < 0:
            continue

        name = _get_string(u, 13, "")
        if not name:
            continue

        prof_data = u.get(16)
        prof_id = 0
        if isinstance(prof_data, bytes):
            pf = _parse_protobuf(prof_data)
            prof_id = _get_int(pf, 3)

        if prof_id in military_profs:
            notable.append({
                "name": name,
                "profession": _get_profession_name(prof_id),
            })

    notable.sort(key=lambda x: x["name"])
    return notable[:limit]


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
        """Get full game state in one call."""
        if not self.client:
            return {"error": "Not connected to DFHack"}

        try:
            # Get all data with minimal RPC calls
            summary = self.client.get_summary()
            view = self.client.get_view_info()
            raw_units = self.client._get_raw_unit_list()

            threats, dead_hostiles = get_threats(raw_units)
            notable = get_notable_citizens(raw_units)

            return {
                "fortress": summary.world_name_english,
                "save": summary.save_name,
                "citizens": summary.citizen_count,
                "idle": summary.idle_count,
                "paused": summary.is_paused,
                "camera": {
                    "x": view.view_x,
                    "y": view.view_y,
                    "z": view.view_z,
                },
                "threats": threats,
                "threat_count": len(threats),
                "dead_hostiles": dead_hostiles,
                "notable": notable,
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

            if after["threat_count"] < before["threat_count"]:
                changes.append(f"Killed {before['threat_count'] - after['threat_count']} invader(s)")
            elif after["threat_count"] > before["threat_count"]:
                changes.append(f"New threats: +{after['threat_count'] - before['threat_count']}")

            if after["dead_hostiles"] > before["dead_hostiles"]:
                changes.append(f"{after['dead_hostiles'] - before['dead_hostiles']} hostile(s) killed")

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
