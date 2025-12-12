#!/usr/bin/env python3
"""Get detailed unit info as JSON. Usage: unit.py <unit_id>"""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient


def main():
    if len(sys.argv) < 2:
        print("Usage: unit.py <unit_id>", file=sys.stderr)
        sys.exit(1)

    unit_id = int(sys.argv[1])

    with DFClient() as client:
        unit = client.get_unit(unit_id)
        if unit:
            print(json.dumps(unit.model_dump(), indent=2))
        else:
            print(json.dumps({"error": f"Unit {unit_id} not found"}))
            sys.exit(1)


if __name__ == "__main__":
    main()
