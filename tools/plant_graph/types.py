"""Railroad plant-graph domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DiagnosticSeverity(str, Enum):
    """Diagnostic classification for the plant parser."""

    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    WARNING = "warning"
    INFO = "info"
@dataclass(frozen=True)
class PlantDocument:
    """Design-document metadata retained independently of source references."""

    title: str = ""
    revision: str = ""
    date: str = ""
    company: str = ""
    comments: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Diagnostic:
    """One parser/validator finding."""

    severity: DiagnosticSeverity
    code: str
    message: str
    entity_ref: str = ""


class EntityKind(str, Enum):
    """Functional entity kinds derived from Railroad symbol types."""

    SWITCH_POWERED = "switch_powered"
    SWITCH_LOCK = "switch_lock"
    DERAIL = "derail"
    IRJ = "irj"
    IRJ_SIGNAL = "irj_signal"
    MAST_SINGLE = "mast_single"
    MAST_DOUBLE = "mast_double"
    MAST_DWARF = "mast_dwarf"
    SIGNAL_HEAD = "signal_head"
    TRACK_CIRCUIT = "track_circuit"
    DIRECTION = "direction"
    OPERATING_POLICY = "operating_policy"
    NEXT_CP = "next_cp"
    BUMPER = "bumper"
    MAIN_HOUSE = "main_house"
    MAINTAINER = "maintainer"
    MAINTAINER_CALL = "maintainer_call"
    ROUTE = "route"
    MILEPOST = "milepost"
    UNKNOWN = "unknown"


class NetClass(str, Enum):
    """Plant-level classification of a KiCad net."""

    TRACK = "track"
    DARK_TRACK = "dark_track"
    SWITCH_OS = "switch_os"  # C/N/R legs covered by derived <switch>T1
    SIGNAL_ATTACHMENT = "signal_attachment"
    HEAD_ATTACHMENT = "head_attachment"
    UNCONNECTED = "unconnected"
    OTHER = "other"


class CircuitRole(str, Enum):
    """A route circuit's operational relationship to its governing mast."""

    ENTRANCE = "entrance"
    HOME_CLEAR = "home_clear"
    DOWNSTREAM = "downstream"
    UNRESOLVED = "unresolved"


class RouteEndKind(str, Enum):
    """How a structural route ends (static enum; for later dynamic eval)."""

    DEAD_END = "dead_end"
    CP_LIMIT = "cp_limit"
    NEXT_FACE = "next_face"
    DARK_EXIT = "dark_exit"

class SchematicHeading(str, Enum):
    """C-to-N heading on the schematic page, without retaining coordinates."""

    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


class TurnoutHand(str, Enum):
    """Side on which the reverse leg lies while looking C-to-N."""

    LEFT = "left"
    RIGHT = "right"


class PointTraversal(str, Enum):
    """Whether a route traverses a turnout through its points or frog."""

    FACING = "facing"
    TRAILING = "trailing"
class TurnoutActuatorKind(str, Enum):
    """The cTc realization used to operate one turnout."""

    SWITCH = "switch"
    LOCK = "lock"

class BoardComponentKind(str, Enum):
    """Physical primitive kinds used by the resolved model-board layout."""

    TURNOUT = "turnout"
    DERAIL = "derail"
    IRJ = "irj"
    SIGNAL = "signal"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class BoardPort:
    """One canonical named attachment point in logical board coordinates."""

    identifier: str
    component_id: str
    name: str
    x_units: float
    row_name: str


@dataclass(frozen=True)
class BoardComponent:
    """One transformed, renderer-neutral model-board appliance."""

    identifier: str
    kind: BoardComponentKind
    label: str
    x_units: float
    row_name: str
    mirror_x: bool = False
    mirror_y: bool = False
    actuator_kind: TurnoutActuatorKind | None = None
    has_frog_lamp: bool = False
    ports: tuple[BoardPort, ...] = ()


@dataclass(frozen=True)
class BoardConnection:
    """One rail segment joining canonical component ports."""

    identifier: str
    row_name: str
    start_port_id: str
    end_port_id: str
    circuit_name: str = ""
    is_dark: bool = False
    is_local_stub: bool = False

@dataclass(frozen=True)
class RailRow:
    """Stable physical board row derived from source topology."""

    name: str
    lane: int
    priority: int
    circuits: tuple[str, ...]


@dataclass(frozen=True)
class RailSpan:
    """One named or switch-OS rail segment assigned to a physical row."""

    name: str
    row_name: str
    endpoints: tuple[str, ...]
    circuit_name: str = ""
    order: int = 0
    start_anchor: int = 0
    end_anchor: int = 0
    endpoint_anchors: tuple[tuple[str, int], ...] = ()
    irj_endpoints: tuple[str, ...] = ()
    turnout_ports: tuple[tuple[str, str, int], ...] = ()
    is_dark: bool = False
    is_local_stub: bool = False
    local_stub_direction: str = ""


@dataclass(frozen=True)
class TurnoutLayout:
    """One turnout's C/N/R ports bound to semantic board rows."""

    switch_name: str
    cn_heading: SchematicHeading
    c_row: str
    n_row: str
    r_row: str
    order: int = 0
    actuator_kind: TurnoutActuatorKind = TurnoutActuatorKind.SWITCH
    has_frog_lamp: bool = True
    actuator_flipped: bool = False
    section_index: int | None = None


@dataclass(frozen=True)
class SignalBase:
    """One mast/head base attached to a signal-IRJ board boundary."""

    mast_name: str
    mast_reference: str
    irj_reference: str
    row_name: str
    direction: str
    anchor: int = 0


@dataclass(frozen=True)
class TrackCircuitLamp:
    """One cTc lamp-hole realization for a named track-circuit span."""

    circuit_name: str
    span_name: str
    row_name: str
    start_anchor: int
    end_anchor: int


@dataclass(frozen=True)
class BoardTerminal:
    """One physical terminal, optionally a composable edge of the plant."""

    name: str
    row_name: str
    side: str
    anchor: int = 0
    is_plant_edge: bool = False
    span_name: str = ""


@dataclass(frozen=True)
class BoardSection:
    """One named logical Main House section in a CTC board."""

    name: str
    index: int
    center_units: float


class Indication(str, Enum):
    """Standard route indication, independent of physical signal aspects."""

    STOP = "STOP"
    UNLIT = "UNLIT"
    RESTRICTING = "RESTRICTING"
    DIVERGING_RESTRICTING = "DIVERGING_RESTRICTING"
    APPROACH = "APPROACH"
    ADVANCED_APPROACH = "ADVANCED_APPROACH"
    DIVERGING_CLEAR = "DIVERGING_CLEAR"
    DIVERGING_ADVANCED_APPROACH = "DIVERGING_ADVANCED_APPROACH"
    DIVERGING_APPROACH = "DIVERGING_APPROACH"
    SECONDARY_DIVERGING_CLEAR = "SECONDARY_DIVERGING_CLEAR"
    SECONDARY_DIVERGING_ADVANCED_APPROACH = (
        "SECONDARY_DIVERGING_ADVANCED_APPROACH"
    )
    SECONDARY_DIVERGING_APPROACH = "SECONDARY_DIVERGING_APPROACH"
    CLEAR = "CLEAR"


@dataclass(frozen=True)
class PlantEntity:
    """One placed railroad symbol instance in the plant graph."""

    reference: str
    kind: EntityKind
    lib_id: str
    value: str
    canonical_name: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlantNet:
    """One net after plant classification."""

    name: str
    net_class: NetClass
    raw_name: str
    nodes: tuple[tuple[str, str], ...]  # (reference, pin)
    authoritative_label: bool


@dataclass(frozen=True)
class DerivedTrackCircuit:
    """Compiler-derived track circuit (not a KiCad net)."""

    name: str
    switch_name: str
    reason: str

@dataclass(frozen=True)
class SwitchGeometry:
    """Source-derived turnout orientation, with no KiCad coordinates retained."""

    switch_name: str
    cn_heading: SchematicHeading
    reverse_side: TurnoutHand


@dataclass(frozen=True)
class SwitchTraversal:
    """One route crossing of a switch, retained in route-travel order."""

    switch_name: str
    entry_pin: str
    exit_pin: str
    alignment: str
    point_traversal: PointTraversal


@dataclass(frozen=True)
class PlantTerminal:
    """Plant entry/exit terminal (DoT or Bumper)."""

    reference: str
    kind: EntityKind
    port_pin: str
    net_name: str
    designation: str
    rulebook: str


@dataclass(frozen=True)
class SignalFace:
    """One mast face of a signal at a Signal IRJ."""

    signal_name: str
    direction: str
    mast_direction: str
    mast_reference: str
    mast_name: str
    irj_reference: str
    approach_pin: str
    plant_pin: str
    approach_net: str
    approach_terminal: str
    head_letters: str = ""  # from mast Value grammar, e.g. AB


@dataclass(frozen=True)
class SignalRoute:
    """One structural plant route equation governed by a signal face.

    Rich enough for later dynamic evaluation: match on switch_alignments,
    require clear_track_circuits vacant, cascade via exit_face_* when
    end_kind is next_face, and resolve display names via PlantGraph.aliases.
    """

    name: str
    signal_name: str
    direction: str
    mast_reference: str
    mast_name: str
    head_letters: str
    entry_terminal: str
    entry_net: str
    entry_designation: str
    entry_rulebook: str
    exit_terminal: str
    exit_net: str
    exit_designation: str
    exit_rulebook: str
    end_kind: RouteEndKind
    exit_face_mast: str
    exit_face_signal: str
    exit_face_direction: str
    switch_alignments: tuple[tuple[str, str], ...]  # (switch_name, N|R)
    circuit_roles: tuple[tuple[str, CircuitRole], ...]
    clear_track_circuits: tuple[str, ...]  # home-clear OS + track circuits
    os_track_circuits: tuple[str, ...]  # derived <switch>T1 on path
    path_track_circuits: tuple[str, ...]  # all labeled track nets traversed
    path_nets: tuple[str, ...]
    head_names: tuple[str, ...] = ()
    static_indication: Indication | None = None
    switch_traversals: tuple[SwitchTraversal, ...] = ()
    derail_requirements: tuple[str, ...] = ()

@dataclass(frozen=True)
class MastHead:
    """One Signal Head attached to a Signal Mast through the netlist."""

    mast_reference: str
    mast_name: str
    mast_pin: str
    head_reference: str
    head_name: str



@dataclass
class PlantGraph:
    """In-memory plant graph projection for one interlocking schematic."""

    entities: dict[str, PlantEntity] = field(default_factory=dict)
    document: PlantDocument = field(default_factory=PlantDocument)
    nets: list[PlantNet] = field(default_factory=list)
    derived_track_circuits: list[DerivedTrackCircuit] = field(default_factory=list)
    switch_geometries: dict[str, SwitchGeometry] = field(default_factory=dict)
    terminals: list[PlantTerminal] = field(default_factory=list)
    signal_faces: list[SignalFace] = field(default_factory=list)
    routes: list[SignalRoute] = field(default_factory=list)
    mast_heads: list[MastHead] = field(default_factory=list)
    rail_rows: list[RailRow] = field(default_factory=list)
    rail_spans: list[RailSpan] = field(default_factory=list)
    turnout_layouts: list[TurnoutLayout] = field(default_factory=list)
    track_circuit_lamps: list[TrackCircuitLamp] = field(default_factory=list)
    signal_bases: list[SignalBase] = field(default_factory=list)
    board_terminals: list[BoardTerminal] = field(default_factory=list)
    board_sections: list[BoardSection] = field(default_factory=list)
    board_width_units: int = 1
    longitudinal_positions: dict[int, float] = field(default_factory=dict)
    board_components: list[BoardComponent] = field(default_factory=list)
    board_connections: list[BoardConnection] = field(default_factory=list)
    mast_direction_map: dict[str, str] = field(
        default_factory=lambda: {
            "N": "LEFT",
            "W": "LEFT",
            "S": "RIGHT",
            "E": "RIGHT",
        }
    )
    diagnostics: list[Diagnostic] = field(default_factory=list)
    # Optional local→display/MP name map (legend). Identity strings stay as drawn.
    name_aliases: dict[str, str] = field(default_factory=dict)

    def errors(self) -> list[Diagnostic]:
        """Return syntax and semantic diagnostics."""
        return [
            d
            for d in self.diagnostics
            if d.severity
            in (DiagnosticSeverity.SYNTAX, DiagnosticSeverity.SEMANTIC)
        ]

    def has_errors(self) -> bool:
        """Return True if any blocking diagnostic exists."""
        return bool(self.errors())

    def display_name(self, identity: str) -> str:
        """Return alias if present, else the graph identity string."""
        return self.name_aliases.get(identity, identity)
