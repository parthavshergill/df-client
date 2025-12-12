#!/usr/bin/env python3
"""Interactive play session - run game and report changes."""

import json
import sys
import time
sys.path.insert(0, "src")

from dfclient.client import DFClient, _parse_protobuf, _get_int, _get_string, _get_profession_name


def get_state(client):
    """Get current game state snapshot."""
    summary = client.get_summary()
    raw_units = client._get_raw_unit_list()

    # Count threats
    threats = []
    dead_hostiles = 0
    for u in raw_units:
        flags1 = _get_int(u, 8)
        flags2 = _get_int(u, 9)
        is_dead = bool(flags1 & 0x2)
        is_invader = bool(flags2 & 0x1) or bool(flags1 & 0x80000)

        if is_invader:
            if is_dead:
                dead_hostiles += 1
            else:
                threats.append(_get_int(u, 1))

    return {
        "citizens": summary.citizen_count,
        "idle": summary.idle_count,
        "paused": summary.is_paused,
        "threats": threats,
        "dead_hostiles": dead_hostiles,
    }


def compare_states(before, after):
    """Compare two state snapshots and describe changes."""
    changes = []

    if after["citizens"] < before["citizens"]:
        changes.append(f"LOST {before['citizens'] - after['citizens']} citizen(s)!")
    elif after["citizens"] > before["citizens"]:
        changes.append(f"Gained {after['citizens'] - before['citizens']} citizen(s)")

    if len(after["threats"]) < len(before["threats"]):
        killed = len(before["threats"]) - len(after["threats"])
        changes.append(f"Killed {killed} invader(s)!")

    if after["dead_hostiles"] > before["dead_hostiles"]:
        new_kills = after["dead_hostiles"] - before["dead_hostiles"]
        changes.append(f"{new_kills} hostile(s) now dead")

    return changes


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    with DFClient() as client:
        before = get_state(client)
        print(f"Before: {before['citizens']} citizens, {len(before['threats'])} threats", file=sys.stderr)

        client.unpause()
        time.sleep(duration)
        client.pause()

        after = get_state(client)
        changes = compare_states(before, after)

        result = {
            "duration_seconds": duration,
            "before": before,
            "after": after,
            "changes": changes if changes else ["No significant changes"],
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
