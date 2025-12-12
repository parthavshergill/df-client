"""Pydantic models for DFHack game state."""

from enum import IntEnum
from pydantic import BaseModel, Field


class UnitFlags(BaseModel):
    """Unit status flags - parsed from flags1/2/3/4 bitfields."""
    dead: bool = False
    caged: bool = False
    tame: bool = False
    merchant: bool = False
    diplomat: bool = False
    on_ground: bool = False
    projectile: bool = False
    active_invader: bool = False
    hidden_ambusher: bool = False
    invader_origin: bool = False


class Position(BaseModel):
    """3D position in the game world."""
    x: int
    y: int
    z: int


class SkillInfo(BaseModel):
    """A unit's skill level."""
    id: int
    name: str = ""
    level: int = 0
    experience: int = 0


class JobInfo(BaseModel):
    """Current job assignment."""
    id: int = 0
    name: str = ""


class Unit(BaseModel):
    """A unit (dwarf, creature, etc.) in the game."""
    id: int
    name: str = ""
    race: str = ""
    position: Position | None = None
    flags: UnitFlags = Field(default_factory=UnitFlags)
    profession: str = ""
    current_job: JobInfo | None = None
    skills: list[SkillInfo] = Field(default_factory=list)
    labors: dict[int, bool] = Field(default_factory=dict)

    @property
    def is_alive(self) -> bool:
        return not self.flags.dead

    @property
    def is_citizen(self) -> bool:
        # Simplified check - in reality need to check civilization
        return self.race.lower() == "dwarf" and self.is_alive and not self.flags.caged


class MapInfo(BaseModel):
    """Information about the current map."""
    block_size_x: int = 0
    block_size_y: int = 0
    block_size_z: int = 0
    block_pos_x: int = 0
    block_pos_y: int = 0
    block_pos_z: int = 0
    world_name: str = ""
    world_name_english: str = ""
    save_name: str = ""


class GameState(BaseModel):
    """Current game state."""
    paused: bool = False
    game_mode: int = 0  # 0 = dwarf mode, etc.
    current_year: int = 0
    current_tick: int = 0
    map_info: MapInfo | None = None
    units: list[Unit] = Field(default_factory=list)

    @property
    def citizens(self) -> list[Unit]:
        """Get all living citizens."""
        return [u for u in self.units if u.is_citizen]


class RPCError(BaseModel):
    """Error response from DFHack RPC."""
    code: int
    message: str


class ConnectionStatus(BaseModel):
    """Status of the connection to DFHack."""
    connected: bool = False
    dfhack_version: str = ""
    df_version: str = ""
    error: str | None = None


# Progressive disclosure models - Layer 1: Summary

class FortressSummary(BaseModel):
    """High-level fortress overview - minimal context cost."""
    world_name: str = ""
    world_name_english: str = ""
    save_name: str = ""
    map_size: tuple[int, int, int] = (0, 0, 0)
    citizen_count: int = 0
    idle_count: int = 0
    animal_count: int = 0
    other_count: int = 0  # invaders, visitors, etc
    is_paused: bool = False


# Progressive disclosure models - Layer 2: Lists

class UnitBrief(BaseModel):
    """Minimal unit info for lists - medium context cost."""
    id: int
    name: str
    profession: str = ""
    is_idle: bool = False

    def __str__(self) -> str:
        idle = " (idle)" if self.is_idle else ""
        return f"[{self.id}] {self.name} - {self.profession}{idle}"


# Progressive disclosure models - Layer 3: Detail

class UnitDetail(BaseModel):
    """Full unit info for single-unit focus - higher context cost."""
    id: int
    name: str
    race: str = ""
    profession: str = ""
    position: Position | None = None
    flags: UnitFlags = Field(default_factory=UnitFlags)
    current_job: str | None = None
    # Skills and labors added in future level


class ViewInfo(BaseModel):
    """Current camera/cursor position."""
    view_x: int = 0
    view_y: int = 0
    view_z: int = 0
    cursor_x: int = -30000  # -30000 = no cursor
    cursor_y: int = -30000
    cursor_z: int = -30000
    follow_unit_id: int = -1  # -1 = not following

    @property
    def has_cursor(self) -> bool:
        return self.cursor_x != -30000
