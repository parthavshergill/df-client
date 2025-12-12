#!/usr/bin/env python3
"""List fortress citizens as JSON."""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient


def main():
    with DFClient() as client:
        citizens = client.get_citizens()
        print(json.dumps([c.model_dump() for c in citizens], indent=2))


if __name__ == "__main__":
    main()
