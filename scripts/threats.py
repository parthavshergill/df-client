#!/usr/bin/env python3
"""Detect hostile units/threats as JSON."""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient, _parse_protobuf, _get_int, _get_string, _get_profession_name


def main():
    with DFClient() as client:
        raw_units = client._get_raw_unit_list()

        threats = []
        for u in raw_units:
            flags1 = _get_int(u, 8)
            flags2 = _get_int(u, 9)

            # Check threat flags
            is_dead = bool(flags1 & 0x2)
            is_active_invader = bool(flags1 & 0x80000)
            is_hidden_ambusher = bool(flags1 & 0x40000)
            is_invader_origin = bool(flags2 & 0x1)

            # Skip dead units and non-threats
            if is_dead:
                continue
            if not (is_active_invader or is_hidden_ambusher or is_invader_origin):
                continue

            unit_id = _get_int(u, 1)
            name = _get_string(u, 13, "Unknown")
            race_id = _get_int(u, 5)
            pos_y = _get_int(u, 3)
            pos_z = _get_int(u, 4)

            # Get profession
            prof_data = u.get(16)
            prof_id = 0
            if isinstance(prof_data, bytes):
                pf = _parse_protobuf(prof_data)
                prof_id = _get_int(pf, 3)

            threat_type = []
            if is_active_invader:
                threat_type.append("active_invader")
            if is_hidden_ambusher:
                threat_type.append("hidden_ambusher")
            if is_invader_origin:
                threat_type.append("invader_origin")

            threats.append({
                "id": unit_id,
                "name": name,
                "race_id": race_id,
                "profession": _get_profession_name(prof_id),
                "position": {"y": pos_y, "z": pos_z},
                "threat_type": threat_type,
            })

        print(json.dumps({
            "threat_count": len(threats),
            "threats": threats
        }, indent=2))


if __name__ == "__main__":
    main()
