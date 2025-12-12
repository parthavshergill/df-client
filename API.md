# DFHack RemoteFortressReader API Reference

## Progressive Disclosure Pattern

The client is designed for **progressive context disclosure** - revealing information in layers:

```
Layer 0: Status   → get_pause_state()     → "Is game paused?"
Layer 1: Summary  → get_summary()         → "49 citizens, 3 idle"
Layer 2: Lists    → get_citizens()        → "[7572] Logem - STANDARD"
Layer 3: Detail   → get_unit(7572)        → Full unit info
```

**Key principle**: Start with summaries, drill down on demand. Don't fetch all details upfront.

## Scripts (JSON output)

Scripts output structured JSON for parsing. Run from df-client directory:

```bash
uv run python scripts/summary.py          # Fortress overview
uv run python scripts/citizens.py         # All citizens
uv run python scripts/idle.py             # Idle citizens only
uv run python scripts/unit.py 7572        # Detail on unit 7572
```

### Example Output

**summary.py**:
```json
{
  "world_name": "Exsmoxsmata",
  "world_name_english": "The Future Realm",
  "save_name": "region2",
  "map_size": [12, 12, 206],
  "citizen_count": 49,
  "idle_count": 3,
  "animal_count": 0,
  "other_count": 0,
  "is_paused": true
}
```

**citizens.py** (excerpt):
```json
[
  {"id": 7572, "name": "Logem Ancientattics", "profession": "STANDARD", "is_idle": false},
  {"id": 7573, "name": "Onol Rocksmanors", "profession": "ELITE_WRESTLER", "is_idle": false}
]
```

**unit.py 7572**:
```json
{
  "id": 7572,
  "name": "Logem Ancientattics",
  "race": "race_178",
  "profession": "STANDARD",
  "position": {"x": 0, "y": 93, "z": 98},
  "flags": {"dead": false, "caged": false, "tame": false, ...},
  "current_job": null
}
```

## Python API

```python
from dfclient import DFClient

with DFClient() as client:
    # Layer 0: Status
    paused = client.get_pause_state()
    client.pause() / client.unpause()

    # Layer 1: Summary (minimal context cost)
    summary = client.get_summary()
    print(f"{summary.citizen_count} citizens, {summary.idle_count} idle")

    # Layer 2: Lists (medium context cost)
    citizens = client.get_citizens()      # All living citizens
    idle = client.get_idle_citizens()     # Idle only

    # Layer 3: Detail (on demand)
    unit = client.get_unit(7572)          # Full details for one unit
```

## Connection

- **Host**: `127.0.0.1:5000` (TCP)
- **Protocol**: Protobuf RPC with length-prefixed messages
- **Handshake**: Send `DFHack?\n` + version(4 bytes LE), receive `DFHack!\n` + version

## Message Format
```
Header: method_id (int16) + padding (2 bytes) + size (uint32 LE)
Body: protobuf-encoded request/response
```

## Core Methods (built-in)
| ID | Method | Input | Output |
|----|--------|-------|--------|
| 0 | BindMethod | CoreBindRequest | CoreBindReply |
| 1 | RunCommand | CoreRunCommandRequest | EmptyMessage |

## RemoteFortressReader Methods
Bind with: `plugin="RemoteFortressReader"`

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| GetPauseState | dfproto.EmptyMessage | RFR.SingleBool | Check if paused |
| SetPauseState | RFR.SingleBool | dfproto.EmptyMessage | Pause/unpause |
| GetVersionInfo | dfproto.EmptyMessage | RFR.VersionInfo | DF/DFHack versions |
| GetMapInfo | dfproto.EmptyMessage | RFR.MapInfo | Map dimensions, world name |
| GetUnitList | dfproto.EmptyMessage | RFR.UnitList | All units |
| GetViewInfo | dfproto.EmptyMessage | RFR.ViewInfo | Current view position |

## CreatureList Field Numbers (from debug)

| Field | Type | Description |
|-------|------|-------------|
| 1 | int | Unit ID |
| 3 | int | pos_y |
| 4 | int | pos_z |
| 5 | int | race_id |
| 6 | submsg | Civ info (field 1 = civ_id) |
| 7 | submsg | Color RGB |
| 8 | int | flags1 |
| 9 | int | flags2 |
| 10 | int | flags3 |
| 11 | int | flags4 |
| 13 | string | Full name |
| 16 | submsg | Profession (field 3 = prof_id) |

## Gotchas

1. **Field 13 is name**: Not field 8 (which is flags1)
2. **Profession in submessage**: Field 16, subfield 3
3. **Children have no name**: Field 13 may be missing for children
4. **Polling required**: No push notifications
5. **Package names**: Core = `dfproto`, RFR = `RemoteFortressReader`
