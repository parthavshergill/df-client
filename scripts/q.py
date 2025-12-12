#!/usr/bin/env python3
"""Query the DFClient daemon.

Usage:
    q.py daemon                - Start the daemon (run first)
    q.py snapshot [radius]     - Get camera-centered game state (default radius=100)
    q.py pause                 - Pause game
    q.py unpause               - Unpause game
    q.py play [seconds]        - Run game for N seconds (default 5)
    q.py tick [ticks]          - Advance game by N ticks (faster, use with timestream)
    q.py run <command>         - Run DFHack console command

Designation Commands (dwarves will act on these):
    q.py dig x1 y1 z1 x2 y2 [type]   - Designate area for digging
                                       types: mine, stair_down, stair_up, stair_updown, channel, ramp
    q.py dig-now                      - Instantly complete all dig designations
    q.py build <type> x y z           - Build workshop/furnace at position
                                       types: carpenter, mason, still, kitchen, craftsdwarf, mechanic, etc.
    q.py stockpile x y z w h <preset> - Create stockpile with preset configuration
                                       presets: all, food, booze, stone, wood, weapons, armor, etc.
    q.py order <job> [amount]         - Create manager work order
                                       jobs: BrewDrink, MakeCharcoal, ConstructBed, etc.
    q.py labor <name> <labor> on|off  - Enable/disable labor for dwarf
                                       labors: MINE, PLANT, BREW, CARPENTER, MASON, HAUL_STONE, etc.
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

    if cmd == "daemon":
        # Start the daemon directly
        from dfclient.daemon import DFDaemon
        daemon = DFDaemon()
        daemon.run()
        return

    if cmd == "snapshot":
        radius = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        request = {"cmd": "snapshot", "radius": radius}
    elif cmd == "pause":
        request = {"cmd": "pause"}
    elif cmd == "unpause":
        request = {"cmd": "unpause"}
    elif cmd == "play":
        seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        request = {"cmd": "play", "seconds": seconds}
    elif cmd == "tick":
        ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        request = {"cmd": "tick", "ticks": ticks}
    elif cmd == "run":
        command = " ".join(sys.argv[2:])
        request = {"cmd": "run", "command": command}
    elif cmd == "quit":
        request = {"cmd": "quit"}
    # Designation commands
    elif cmd == "dig":
        # dig x1 y1 z1 x2 y2 [type]
        if len(sys.argv) < 7:
            print("Usage: dig x1 y1 z1 x2 y2 [type]")
            print("Types: mine, stair_down, stair_up, stair_updown, channel, ramp")
            sys.exit(1)
        x1, y1, z1, x2, y2 = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
        dig_type = sys.argv[7] if len(sys.argv) > 7 else "mine"
        request = {"cmd": "dig", "x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "type": dig_type}
    elif cmd == "dig-now":
        request = {"cmd": "dig-now"}
    elif cmd == "build":
        # build <type> x y z
        if len(sys.argv) < 6:
            print("Usage: build <type> x y z")
            print("Types: carpenter, mason, still, kitchen, craftsdwarf, mechanic, butcher, tanner, leather, clothier, fishery, farmer, jeweler, loom, dyer, bowyer, siege, kennel, ashery, tool, metalsmith, furnace_smelter, furnace_wood, furnace_glass, furnace_kiln")
            sys.exit(1)
        build_type = sys.argv[2]
        x, y, z = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        request = {"cmd": "build", "type": build_type, "x": x, "y": y, "z": z}
    elif cmd == "stockpile":
        # stockpile x y z w h <preset>
        if len(sys.argv) < 8:
            print("Usage: stockpile x y z width height <preset>")
            print("Presets: all, food, booze, seeds, stone, wood, weapons, armor, ammo, furniture, bars, gems, cloth, leather, finished_goods, refuse, corpses, animals, coins")
            sys.exit(1)
        x, y, z = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        w, h = int(sys.argv[5]), int(sys.argv[6])
        preset = sys.argv[7]
        request = {"cmd": "stockpile", "x": x, "y": y, "z": z, "width": w, "height": h, "preset": preset}
    elif cmd == "order":
        # order <job> [amount]
        if len(sys.argv) < 3:
            print("Usage: order <job_type> [amount]")
            print("Common jobs: BrewDrink, ProcessPlants, ConstructBed, MakeBarrel, MakeBin, ConstructChair, ConstructTable, ConstructDoor, ConstructCabinet, MakeCharcoal, SmeltOre")
            sys.exit(1)
        job_type = sys.argv[2]
        amount = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        request = {"cmd": "order", "job": job_type, "amount": amount}
    elif cmd == "labor":
        # labor <name> <labor> on|off
        if len(sys.argv) < 5:
            print("Usage: labor <dwarf_name> <labor_type> on|off")
            print("Labors: MINE, HAUL_STONE, HAUL_WOOD, HAUL_BODY, HAUL_FOOD, HAUL_REFUSE, HAUL_ITEM, HAUL_FURNITURE, HAUL_ANIMALS, CUTWOOD, CARPENTER, DETAIL, MASON, ARCHITECT, ANIMALTRAIN, ANIMALCARE, DIAGNOSE, SURGERY, BONE_SETTING, SUTURING, DRESSING_WOUNDS, FEED_WATER_CIVILIANS, RECOVER_WOUNDED, BUTCHER, TRAPPER, SMALL_ANIMAL_DISSECTION, LEATHER, TANNER, BREWER, ALCHEMIST, SOAP_MAKER, WEAVER, CLOTHESMAKER, MILLER, PROCESS_PLANT, MAKE_CHEESE, COOK, PLANT, HERBALIST, FISH, CLEAN_FISH, DISSECT_FISH, HUNT, SMELT, FORGE_WEAPON, FORGE_ARMOR, FORGE_FURNITURE, METAL_CRAFT, CUT_GEM, ENCRUST_GEM, WOOD_CRAFT, STONE_CRAFT, BONE_CARVE, GLAZING, PRESSING, STRAND_EXTRACTION, BEEKEEPING, WAX_WORKING, PAPERMAKING, BOOKBINDING")
            sys.exit(1)
        dwarf_name = sys.argv[2]
        labor_type = sys.argv[3]
        enabled = sys.argv[4].lower() in ("on", "true", "1", "yes")
        request = {"cmd": "labor", "name": dwarf_name, "labor": labor_type, "enabled": enabled}
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
