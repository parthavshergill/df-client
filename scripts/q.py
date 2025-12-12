#!/usr/bin/env python3
"""Query the DFClient daemon.

Usage:
    q.py snapshot              - Get full game state
    q.py pause                 - Pause game
    q.py unpause               - Unpause game
    q.py play [seconds]        - Run game for N seconds (default 5)
    q.py run <command>         - Run DFHack console command
"""

import json
import socket
import sys

DAEMON_PORT = 5001


def query(request: dict) -> dict:
    """Send a request to the daemon and return the response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(120)  # Long timeout for play commands
    try:
        sock.connect(("127.0.0.1", DAEMON_PORT))
        sock.sendall(json.dumps(request).encode("utf-8") + b"\n")

        # Read response
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk

        return json.loads(data.decode("utf-8"))
    finally:
        sock.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "snapshot":
        request = {"cmd": "snapshot"}
    elif cmd == "pause":
        request = {"cmd": "pause"}
    elif cmd == "unpause":
        request = {"cmd": "unpause"}
    elif cmd == "play":
        seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        request = {"cmd": "play", "seconds": seconds}
    elif cmd == "run":
        command = " ".join(sys.argv[2:])
        request = {"cmd": "run", "command": command}
    elif cmd == "quit":
        request = {"cmd": "quit"}
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

    try:
        response = query(request)
        print(json.dumps(response, indent=2))
    except ConnectionRefusedError:
        print('{"ok": false, "error": "Daemon not running. Start with: uv run python scripts/daemon.py"}')
        sys.exit(1)
    except Exception as e:
        print(f'{{"ok": false, "error": "{e}"}}')
        sys.exit(1)


if __name__ == "__main__":
    main()
