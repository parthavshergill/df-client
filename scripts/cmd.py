#!/usr/bin/env python3
"""Run a DFHack command and print output."""

import sys
import time
sys.path.insert(0, "src")

from dfclient.client import DFClient


def main():
    if len(sys.argv) < 2:
        print("Usage: cmd.py <command>", file=sys.stderr)
        sys.exit(1)

    command = " ".join(sys.argv[1:])

    with DFClient() as client:
        # Pause for safety
        was_paused = client.get_pause_state()
        if not was_paused:
            client.pause()
            time.sleep(1)

        result = client.run_command(command, timeout=10.0)

        for line in result:
            print(line)

        # Restore pause state
        if not was_paused:
            client.unpause()


if __name__ == "__main__":
    main()
