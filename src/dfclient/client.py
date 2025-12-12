"""High-level DFHack client API."""

import struct
from typing import Any

from dfclient.connection import DFHackConnection
from dfclient.models import (
    ConnectionStatus,
    FortressSummary,
    MapInfo,
    Position,
    UnitBrief,
    UnitDetail,
    UnitFlags,
    ViewInfo,
)


# Core protocol method IDs (built-in)
CORE_BIND_METHOD = 0
CORE_RUN_COMMAND = 1
CORE_RUN_LUA = 2

# Profession lookup table (from DF profession_type enum)
PROFESSIONS: dict[int, str] = {
    0: "NONE",
    1: "MINER",
    2: "WOODWORKER",
    3: "CARPENTER",
    4: "BOWYER",
    5: "WOODCUTTER",
    6: "STONEWORKER",
    7: "ENGRAVER",
    8: "MASON",
    9: "METALSMITH",
    10: "WEAPONSMITH",
    11: "ARMORSMITH",
    12: "BLACKSMITH",
    13: "METALCRAFTER",
    14: "JEWELER",
    15: "GEM_CUTTER",
    16: "GEM_SETTER",
    17: "CRAFTSMAN",
    18: "WOODCRAFTER",
    19: "STONECRAFTER",
    20: "LEATHERWORKER",
    21: "BONE_CARVER",
    22: "WEAVER",
    23: "CLOTHIER",
    24: "GLASSMAKER",
    25: "POTTER",
    26: "GLAZER",
    27: "WAX_WORKER",
    28: "STRAND_EXTRACTOR",
    29: "FISHERY_WORKER",
    30: "FISH_CLEANER",
    31: "FISH_DISSECTOR",
    32: "RANGER",
    33: "ANIMAL_CARETAKER",
    34: "ANIMAL_TRAINER",
    35: "HUNTER",
    36: "TRAPPER",
    37: "ANIMAL_DISSECTOR",
    38: "CHEESE_MAKER",
    39: "MILKER",
    40: "COOK",
    41: "THRESHER",
    42: "MILLER",
    43: "BUTCHER",
    44: "TANNER",
    45: "DYER",
    46: "PLANTER",
    47: "HERBALIST",
    48: "BREWER",
    49: "SOAP_MAKER",
    50: "POTASH_MAKER",
    51: "LYE_MAKER",
    52: "WOOD_BURNER",
    53: "SHEARER",
    54: "SPINNER",
    55: "PRESSER",
    56: "BEEKEEPER",
    57: "ENGINEER",
    58: "MECHANIC",
    59: "SIEGE_ENGINEER",
    60: "SIEGE_OPERATOR",
    61: "PUMP_OPERATOR",
    62: "CLERK",
    63: "ADMINISTRATOR",
    64: "TRADER",
    65: "ARCHITECT",
    66: "ALCHEMIST",
    67: "DOCTOR",
    68: "DIAGNOSER",
    69: "BONE_SETTER",
    70: "SUTURER",
    71: "SURGEON",
    72: "MERCHANT",
    73: "HAMMERMAN",
    74: "SPEARMAN",
    75: "CROSSBOWMAN",
    76: "WRESTLER",
    77: "AXEMAN",
    78: "SWORDSMAN",
    79: "MACEMAN",
    80: "PIKEMAN",
    81: "BOWMAN",
    82: "BLOWGUNMAN",
    83: "LASHER",
    84: "RECRUIT",
    85: "TRAINED_HUNTER",
    86: "TRAINED_WAR",
    87: "MASTER_HAMMERMAN",
    88: "MASTER_SPEARMAN",
    89: "MASTER_CROSSBOWMAN",
    90: "MASTER_WRESTLER",
    91: "MASTER_AXEMAN",
    92: "MASTER_SWORDSMAN",
    93: "MASTER_MACEMAN",
    94: "MASTER_PIKEMAN",
    95: "MASTER_BOWMAN",
    96: "MASTER_BLOWGUNMAN",
    97: "MASTER_LASHER",
    98: "ELITE_HAMMERMAN",
    99: "ELITE_SPEARMAN",
    100: "ELITE_CROSSBOWMAN",
    101: "ELITE_WRESTLER",
    102: "ELITE_AXEMAN",
    103: "CHILD",
    104: "BABY",
    105: "DRUNK",
    106: "MONSTER_SLAYER",
    107: "SCOUT",
    108: "BEAST_HUNTER",
    109: "SNATCHER",
    110: "MERCENARY",
    111: "THIEF",
    112: "PRISONER",
    113: "SLAVE",
    114: "STANDARD",
    115: "SAGE",
    116: "SCHOLAR",
    117: "PHILOSOPHER",
    118: "MATHEMATICIAN",
    119: "HISTORIAN",
    120: "ASTRONOMER",
    121: "NATURALIST",
    122: "CHEMIST",
    123: "GEOGRAPHER",
    124: "SCRIBE",
    125: "PERFORMER",
    126: "POET",
    127: "BARD",
    128: "DANCER",
    129: "CRIMINAL",
}


def _encode_varint(value: int) -> bytes:
    """Encode an integer as a protobuf varint."""
    parts = []
    while value > 127:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)


def _decode_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode a protobuf varint, return (value, bytes_consumed)."""
    result = 0
    shift = 0
    pos = offset
    while True:
        if pos >= len(data):
            raise ValueError("Truncated varint")
        byte = data[pos]
        result |= (byte & 0x7F) << shift
        pos += 1
        if not (byte & 0x80):
            break
        shift += 7
    return result, pos - offset


def _encode_string(field_num: int, value: str) -> bytes:
    """Encode a string field in protobuf format."""
    encoded = value.encode("utf-8")
    tag = (field_num << 3) | 2  # wire type 2 = length-delimited
    return _encode_varint(tag) + _encode_varint(len(encoded)) + encoded


def _encode_bind_request(method: str, input_msg: str, output_msg: str, plugin: str = "") -> bytes:
    """Encode a CoreBindRequest protobuf message."""
    # Fields: method (1), input_msg (2), output_msg (3), plugin (4)
    data = _encode_string(1, method)
    data += _encode_string(2, input_msg)
    data += _encode_string(3, output_msg)
    if plugin:
        data += _encode_string(4, plugin)
    return data


def _decode_bind_reply(data: bytes) -> int:
    """Decode a CoreBindReply to get the assigned method ID."""
    # Field 1 is assigned_id (int32)
    pos = 0
    while pos < len(data):
        tag, consumed = _decode_varint(data, pos)
        pos += consumed
        field_num = tag >> 3
        wire_type = tag & 0x7

        if field_num == 1 and wire_type == 0:  # varint
            value, consumed = _decode_varint(data, pos)
            # Handle signed int32 (zigzag would be different, but this is regular int32)
            if value > 0x7FFFFFFF:
                value -= 0x100000000
            return value
        elif wire_type == 0:
            _, consumed = _decode_varint(data, pos)
            pos += consumed
        elif wire_type == 2:
            length, consumed = _decode_varint(data, pos)
            pos += consumed + length
        else:
            raise ValueError(f"Unknown wire type {wire_type}")

    raise ValueError("assigned_id not found in reply")


def _parse_protobuf(data: bytes) -> dict[int, Any]:
    """Parse protobuf bytes into field_num -> value dict.

    Returns dict where:
    - Varint fields (wire type 0) -> int
    - Length-delimited fields (wire type 2) -> bytes (for strings/submessages)
    - Repeated fields -> list of values
    """
    result: dict[int, Any] = {}
    pos = 0

    while pos < len(data):
        tag, consumed = _decode_varint(data, pos)
        pos += consumed
        field_num = tag >> 3
        wire_type = tag & 0x7

        if wire_type == 0:  # varint
            value, consumed = _decode_varint(data, pos)
            pos += consumed
        elif wire_type == 2:  # length-delimited
            length, consumed = _decode_varint(data, pos)
            pos += consumed
            value = data[pos:pos + length]
            pos += length
        elif wire_type == 5:  # 32-bit fixed
            value = struct.unpack("<I", data[pos:pos+4])[0]
            pos += 4
        elif wire_type == 1:  # 64-bit fixed
            value = struct.unpack("<Q", data[pos:pos+8])[0]
            pos += 8
        else:
            raise ValueError(f"Unknown wire type {wire_type}")

        # Handle repeated fields
        if field_num in result:
            if not isinstance(result[field_num], list):
                result[field_num] = [result[field_num]]
            result[field_num].append(value)
        else:
            result[field_num] = value

    return result


def _get_string(fields: dict[int, Any], field_num: int, default: str = "") -> str:
    """Get a string field from parsed protobuf."""
    if field_num not in fields:
        return default
    val = fields[field_num]
    if isinstance(val, bytes):
        # Try to decode as string first
        try:
            decoded = val.decode("utf-8", errors="replace")
            if decoded.isprintable() and len(decoded) > 0:
                return decoded
        except:
            pass
        # Might be a submessage - try to parse and look for string in field 10
        try:
            subfields = _parse_protobuf(val)
            if 10 in subfields and isinstance(subfields[10], bytes):
                return subfields[10].decode("utf-8", errors="replace")
        except:
            pass
    return default


def _get_int(fields: dict[int, Any], field_num: int, default: int = 0) -> int:
    """Get an int field from parsed protobuf."""
    return fields.get(field_num, default)


def _get_profession_name(prof_id: int) -> str:
    """Get human-readable profession name."""
    return PROFESSIONS.get(prof_id, f"UNKNOWN_{prof_id}")


class DFClient:
    """High-level client for interacting with Dwarf Fortress via DFHack."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.host = host
        self.port = port
        self._conn = DFHackConnection(host, port)
        self._method_ids: dict[str, int] = {}

    def connect(self) -> ConnectionStatus:
        """Connect to DFHack."""
        return self._conn.connect()

    def disconnect(self) -> None:
        """Disconnect from DFHack."""
        self._conn.disconnect()

    def _bind_method(self, method: str, input_msg: str, output_msg: str, plugin: str = "") -> int:
        """Bind a method and return its assigned ID."""
        cache_key = f"{plugin}:{method}"
        if cache_key in self._method_ids:
            return self._method_ids[cache_key]

        request = _encode_bind_request(method, input_msg, output_msg, plugin)
        reply = self._conn.call(CORE_BIND_METHOD, request)
        method_id = _decode_bind_reply(reply)
        self._method_ids[cache_key] = method_id
        return method_id

    def run_command(self, command: str, timeout: float | None = None) -> list[str]:
        """
        Run a DFHack console command.

        Args:
            command: The command to run (e.g., "ls", "kill-unit 123")
            timeout: Optional timeout override (some commands don't return results)

        Returns:
            List of output lines
        """
        output_lines: list[str] = []

        def collect_output(text: str) -> None:
            output_lines.extend(text.splitlines())

        # Parse command into name and arguments
        # CoreRunCommandRequest: command (1) = string, arguments (2) = repeated string
        import shlex

        # Special case: "lua" command - pass entire code as single argument
        if command.startswith("lua "):
            cmd_name = "lua"
            cmd_args = [command[4:]]  # Everything after "lua "
        else:
            try:
                parts = shlex.split(command)
            except ValueError:
                parts = command.split()
            cmd_name = parts[0] if parts else command
            cmd_args = parts[1:] if len(parts) > 1 else []

        # Encode: field 1 = command name, field 2 (repeated) = arguments
        request = _encode_string(1, cmd_name)
        for arg in cmd_args:
            request += _encode_string(2, arg)

        # Some commands (like clean, prospect) don't return a RESULT
        # Use shorter timeout and accept timeout as success for those
        old_timeout = self._conn._socket.gettimeout() if self._conn._socket else 30.0
        if timeout is not None and self._conn._socket:
            self._conn._socket.settimeout(timeout)

        try:
            self._conn.call(CORE_RUN_COMMAND, request, text_callback=collect_output)
        except TimeoutError:
            # For fire-and-forget commands, timeout is acceptable
            pass
        finally:
            if self._conn._socket:
                self._conn._socket.settimeout(old_timeout)

        return output_lines

    def get_pause_state(self) -> bool:
        """Get whether the game is currently paused."""
        method_id = self._bind_method(
            "GetPauseState",
            "dfproto.EmptyMessage",
            "RemoteFortressReader.SingleBool",
            plugin="RemoteFortressReader",
        )

        reply = self._conn.call(method_id, b"")
        # SingleBool: value (1) = bool (varint)
        if reply:
            value, _ = _decode_varint(reply, 0)
            # Skip tag byte(s) to get to the value
            pos = 0
            while pos < len(reply):
                tag, consumed = _decode_varint(reply, pos)
                pos += consumed
                field_num = tag >> 3
                wire_type = tag & 0x7
                if field_num == 1 and wire_type == 0:
                    value, _ = _decode_varint(reply, pos)
                    return bool(value)
                elif wire_type == 0:
                    _, consumed = _decode_varint(reply, pos)
                    pos += consumed
        return False

    def set_pause_state(self, paused: bool) -> None:
        """Set the game pause state."""
        method_id = self._bind_method(
            "SetPauseState",
            "RemoteFortressReader.SingleBool",
            "dfproto.EmptyMessage",
            plugin="RemoteFortressReader",
        )

        # SingleBool: value (1) = bool
        tag = (1 << 3) | 0  # field 1, varint
        request = _encode_varint(tag) + _encode_varint(1 if paused else 0)

        self._conn.call(method_id, request)

    def pause(self) -> None:
        """Pause the game."""
        self.set_pause_state(True)

    def unpause(self) -> None:
        """Unpause the game."""
        self.set_pause_state(False)

    def get_version_info(self) -> dict[str, str]:
        """Get DFHack and DF version information."""
        method_id = self._bind_method(
            "GetVersionInfo",
            "dfproto.EmptyMessage",
            "RemoteFortressReader.VersionInfo",
            plugin="RemoteFortressReader",
        )

        reply = self._conn.call(method_id, b"")

        # Parse VersionInfo
        result = {"dfhack_version": "", "df_version": ""}
        pos = 0
        while pos < len(reply):
            tag, consumed = _decode_varint(reply, pos)
            pos += consumed
            field_num = tag >> 3
            wire_type = tag & 0x7

            if wire_type == 2:  # length-delimited (string)
                length, consumed = _decode_varint(reply, pos)
                pos += consumed
                value = reply[pos : pos + length].decode("utf-8", errors="replace")
                pos += length

                if field_num == 1:
                    result["dfhack_version"] = value
                elif field_num == 2:
                    result["df_version"] = value
            elif wire_type == 0:
                _, consumed = _decode_varint(reply, pos)
                pos += consumed

        return result

    def get_map_info(self) -> MapInfo:
        """Get map dimensions and world name."""
        method_id = self._bind_method(
            "GetMapInfo",
            "dfproto.EmptyMessage",
            "RemoteFortressReader.MapInfo",
            plugin="RemoteFortressReader",
        )

        reply = self._conn.call(method_id, b"")
        fields = _parse_protobuf(reply)

        # MapInfo fields:
        # 1: block_size_x, 2: block_size_y, 3: block_size_z
        # 4: block_pos_x, 5: block_pos_y, 6: block_pos_z
        # 7: world_name, 8: world_name_english, 9: save_name
        return MapInfo(
            block_size_x=_get_int(fields, 1),
            block_size_y=_get_int(fields, 2),
            block_size_z=_get_int(fields, 3),
            block_pos_x=_get_int(fields, 4),
            block_pos_y=_get_int(fields, 5),
            block_pos_z=_get_int(fields, 6),
            world_name=_get_string(fields, 7),
            world_name_english=_get_string(fields, 8),
            save_name=_get_string(fields, 9),
        )

    def get_view_info(self) -> ViewInfo:
        """Get current camera/cursor position."""
        method_id = self._bind_method(
            "GetViewInfo",
            "dfproto.EmptyMessage",
            "RemoteFortressReader.ViewInfo",
            plugin="RemoteFortressReader",
        )

        reply = self._conn.call(method_id, b"")
        fields = _parse_protobuf(reply)

        # ViewInfo fields:
        # 1: view_pos_x, 2: view_pos_y, 3: view_pos_z
        # 4: cursor_pos_x, 5: cursor_pos_y, 6: cursor_pos_z
        # 7: follow_unit_id
        return ViewInfo(
            view_x=_get_int(fields, 1),
            view_y=_get_int(fields, 2),
            view_z=_get_int(fields, 3),
            cursor_x=_get_int(fields, 4, -30000),
            cursor_y=_get_int(fields, 5, -30000),
            cursor_z=_get_int(fields, 6, -30000),
            follow_unit_id=_get_int(fields, 7, -1),
        )

    def _get_raw_unit_list(self) -> list[dict[int, Any]]:
        """Get raw unit list data (internal)."""
        method_id = self._bind_method(
            "GetUnitList",
            "dfproto.EmptyMessage",
            "RemoteFortressReader.UnitList",
            plugin="RemoteFortressReader",
        )

        reply = self._conn.call(method_id, b"")
        fields = _parse_protobuf(reply)

        # UnitList field 1 = repeated CreatureList
        creatures_raw = fields.get(1, [])
        if not isinstance(creatures_raw, list):
            creatures_raw = [creatures_raw]

        units = []
        for creature_bytes in creatures_raw:
            if isinstance(creature_bytes, bytes):
                units.append(_parse_protobuf(creature_bytes))
        return units

    def _parse_unit_name(self, name_bytes: bytes) -> str:
        """Parse NameTriple to string."""
        if not name_bytes:
            return ""
        fields = _parse_protobuf(name_bytes)
        # NameTriple: 1=first_name, 2=nickname, 3=last_name
        first = _get_string(fields, 1)
        nick = _get_string(fields, 2)
        last = _get_string(fields, 3)

        if nick:
            return f'"{nick}"'
        elif first:
            return first.capitalize()
        elif last:
            return last.capitalize()
        return "Unknown"

    def _get_profession_id(self, unit_fields: dict[int, Any]) -> int:
        """Extract profession ID from unit fields."""
        # Field 16 is a submessage containing profession info
        # Subfield 3 within it is the profession_id
        prof_data = unit_fields.get(16)
        if isinstance(prof_data, bytes):
            prof_fields = _parse_protobuf(prof_data)
            return _get_int(prof_fields, 3)
        return 0

    def get_all_units(self) -> list[UnitBrief]:
        """Get all units as brief summaries."""
        raw_units = self._get_raw_unit_list()
        result = []

        for u in raw_units:
            # CreatureList fields (from debug analysis):
            # 1: id, 3: pos_y, 4: pos_z, 5: race_id
            # 6: mat submsg (civ info?), 7: color RGB
            # 8: flags1, 9: flags2, 10: flags3, 11: flags4
            # 13: name (string!)
            # 16: profession submsg (field 3 = prof_id)
            # 17: squad/group?, 25: age?
            unit_id = _get_int(u, 1)

            # Field 13 is the name as a string
            name = _get_string(u, 13, "Unknown")

            # Check flags for idle/dead status
            flags1 = _get_int(u, 8)
            is_dead = bool(flags1 & 0x2)  # bit 1 = dead

            # Get profession ID from submessage
            prof_id = self._get_profession_id(u)
            is_idle = prof_id == 103 or prof_id == 0

            result.append(UnitBrief(
                id=unit_id,
                name=name,
                profession=_get_profession_name(prof_id),
                is_idle=is_idle and not is_dead,
            ))

        return result

    def _get_civ_id(self, unit_fields: dict[int, Any]) -> int:
        """Extract civilization ID from unit fields."""
        # Field 6 is a submessage, subfield 1 is the civ_id
        civ_data = unit_fields.get(6)
        if isinstance(civ_data, bytes):
            civ_fields = _parse_protobuf(civ_data)
            return _get_int(civ_fields, 1, -1)
        return -1

    def get_citizens(self) -> list[UnitBrief]:
        """Get fortress citizens only (living dwarves)."""
        raw_units = self._get_raw_unit_list()
        result = []

        for u in raw_units:
            # Check if this is a citizen using correct field numbers
            flags1 = _get_int(u, 8)   # flags1
            flags2 = _get_int(u, 9)   # flags2

            is_dead = bool(flags1 & 0x2)
            is_merchant = bool(flags1 & 0x40)
            is_diplomat = bool(flags2 & 0x800000)
            is_invader = bool(flags1 & 0x80000)

            # Skip non-citizens
            if is_dead or is_merchant or is_diplomat or is_invader:
                continue

            # Check civilization - civ_id > 0 means belongs to a civilization
            civ_id = self._get_civ_id(u)
            if civ_id < 0:
                continue  # Wild animal

            unit_id = _get_int(u, 1)
            name = _get_string(u, 13, "Unknown")

            prof_id = self._get_profession_id(u)
            is_idle = prof_id == 103 or prof_id == 0

            result.append(UnitBrief(
                id=unit_id,
                name=name,
                profession=_get_profession_name(prof_id),
                is_idle=is_idle,
            ))

        return result

    def get_idle_citizens(self) -> list[UnitBrief]:
        """Get idle citizens only."""
        return [u for u in self.get_citizens() if u.is_idle]

    def get_unit(self, unit_id: int) -> UnitDetail | None:
        """Get detailed info for a specific unit."""
        raw_units = self._get_raw_unit_list()

        for u in raw_units:
            if _get_int(u, 1) != unit_id:
                continue

            # Found the unit - parse full details using correct field numbers
            name = _get_string(u, 13, "Unknown")

            flags1 = _get_int(u, 8)   # flags1
            flags2 = _get_int(u, 9)   # flags2

            prof_id = self._get_profession_id(u)

            return UnitDetail(
                id=unit_id,
                name=name,
                race=f"race_{_get_int(u, 5)}",  # TODO: lookup race name
                profession=_get_profession_name(prof_id),
                position=Position(
                    x=0,  # pos_x not in data, might be field 2 or missing
                    y=_get_int(u, 3),
                    z=_get_int(u, 4),
                ),
                flags=UnitFlags(
                    dead=bool(flags1 & 0x2),
                    caged=bool(flags1 & 0x200000),
                    tame=bool(flags1 & 0x400),
                    merchant=bool(flags1 & 0x40),
                    diplomat=bool(flags2 & 0x800000),
                    active_invader=bool(flags1 & 0x80000),
                ),
                current_job=None,  # TODO: parse job info
            )

        return None

    def get_summary(self) -> FortressSummary:
        """Get high-level fortress summary - minimal context cost."""
        map_info = self.get_map_info()
        is_paused = self.get_pause_state()

        # Get unit counts using correct field numbers
        raw_units = self._get_raw_unit_list()

        citizen_count = 0
        idle_count = 0
        animal_count = 0
        other_count = 0

        for u in raw_units:
            flags1 = _get_int(u, 8)   # flags1
            flags2 = _get_int(u, 9)   # flags2
            civ_id = self._get_civ_id(u)
            prof_id = self._get_profession_id(u)

            is_dead = bool(flags1 & 0x2)
            if is_dead:
                continue

            is_merchant = bool(flags1 & 0x40)
            is_diplomat = bool(flags2 & 0x800000)
            is_invader = bool(flags1 & 0x80000)

            if civ_id < 0:
                animal_count += 1
            elif is_merchant or is_diplomat or is_invader:
                other_count += 1
            else:
                citizen_count += 1
                if prof_id == 103 or prof_id == 0:
                    idle_count += 1

        return FortressSummary(
            world_name=map_info.world_name,
            world_name_english=map_info.world_name_english,
            save_name=map_info.save_name,
            map_size=(map_info.block_size_x, map_info.block_size_y, map_info.block_size_z),
            citizen_count=citizen_count,
            idle_count=idle_count,
            animal_count=animal_count,
            other_count=other_count,
            is_paused=is_paused,
        )

    def __enter__(self) -> "DFClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
