#!/usr/bin/env python3
"""Get fortress summary as JSON."""

import json
import sys
sys.path.insert(0, "src")

from dfclient.client import DFClient


def main():
    with DFClient() as client:
        summary = client.get_summary()
        print(json.dumps(summary.model_dump(), indent=2))


if __name__ == "__main__":
    main()
