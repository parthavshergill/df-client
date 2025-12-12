#!/usr/bin/env python3
"""Comprehensive fortress status report as JSON."""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient, _parse_protobuf, _get_int, _get_string, _get_profession_name


def get_threats(raw_units):
    """Extract threat information from units."""
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
        })

    return threats, dead_hostiles


def get_notable_citizens(raw_units, limit=5):
    """Get notable citizens (military, skilled)."""
    military_profs = {73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83,  # Basic military
                      87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97,  # Masters
                      98, 99, 100, 101, 102}  # Elite

    notable = []
    for u in raw_units:
        flags1 = _get_int(u, 8)
        is_dead = bool(flags1 & 0x2)
        if is_dead:
            continue

        # Check civilization
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

        # Prioritize military
        if prof_id in military_profs:
            notable.append({
                "name": name,
                "profession": _get_profession_name(prof_id),
                "is_military": True
            })

    # Return top notable (sorted by military first)
    notable.sort(key=lambda x: (not x.get("is_military", False), x["name"]))
    return notable[:limit]


def main():
    with DFClient() as client:
        # Get basic summary
        summary = client.get_summary()

        # Get raw units for detailed analysis
        raw_units = client._get_raw_unit_list()

        # Get threats
        threats, dead_hostiles = get_threats(raw_units)

        # Get notable citizens
        notable = get_notable_citizens(raw_units)

        status = {
            "fortress": {
                "name": summary.world_name_english,
                "name_dwarvish": summary.world_name,
                "save": summary.save_name,
            },
            "population": {
                "citizens": summary.citizen_count,
                "idle": summary.idle_count,
                "animals": summary.animal_count,
                "visitors": summary.other_count,
            },
            "military": {
                "active_threats": len(threats),
                "threats": threats,
                "dead_hostiles": dead_hostiles,
            },
            "notable_citizens": notable,
            "game_state": {
                "paused": summary.is_paused,
                "map_size": list(summary.map_size),
            }
        }

        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
