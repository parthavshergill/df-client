#!/usr/bin/env python3
"""List idle citizens as JSON."""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient


def main():
    with DFClient() as client:
        idle = client.get_idle_citizens()
        print(json.dumps([c.model_dump() for c in idle], indent=2))


if __name__ == "__main__":
    main()
