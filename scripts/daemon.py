#!/usr/bin/env python3
"""Start the DFClient daemon for fast queries."""

import sys
sys.path.insert(0, "src")

from dfclient.daemon import main

if __name__ == "__main__":
    main()
