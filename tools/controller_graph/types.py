"""Domain types for the controller fragment.

The fragment is the per-project compile output: local facts only, no
cross-project knowledge. Roles come from hidden Role/Kind fields; Value is
the name; References are netlist identities only.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Machine:
    """The one MACHINE symbol in a controller project."""

    name: str
    machine_type: str
    columns: int


@dataclass(frozen=True)
class Column:
    """A panel column. A column IS a controlled point."""

    number: int
    cp_name: str
    interlocking: str


@dataclass(frozen=True)
class Appliance:
    """A panel appliance (lever, lamp, code button, aux) on one column."""

    reference: str
    kind: str
    name: str
    column: int
    interlocking: str
    indication_tokens: tuple[str, ...] = ()
    control_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Diagnostic:
    """One compile or link finding. Emission is never blocked by findings;
    consumers decide what is fatal for their output."""

    severity: str  # "error" | "warning" | "info"
    code: str  # stable identifier, e.g. "netlist-no-nets"
    subject: str  # reference, name, or sheet the finding is about
    message: str


def station_key(station: str) -> str:
    """Wire key: whitespace removed, case folded ('Gilroy CalTrain' ->
    'gilroycaltrain'). Names stay case-preserved everywhere else."""
    return "".join(station.split()).lower()


@dataclass(frozen=True)
class Codeline:
    """The one CODELINE symbol on an interlocking sheet.

    A sheet holding a codeline and nothing else is a recognized stub: a
    declared placeholder for an interlocking not yet drawn on this panel.
    """

    interlocking: str
    transport: str  # Codeline Value: VIRTUAL, MQTT, CMRInet, ...
    station: str
    stub: bool
    params: dict[str, str] = field(default_factory=dict)

    @property
    def station_key(self) -> str:
        return station_key(self.station)


@dataclass(frozen=True)
class DriveBinding:
    """One appliance function pin wired to one IODRIVER bit."""

    appliance: str  # appliance reference (netlist identity)
    function: str  # NWS, RWK, LAMP, CODE, SW, ...
    driver: str  # IODRIVER Value, e.g. "0x24"
    bus_kind: str  # e.g. "I2C-MAX7313"
    bit: int


@dataclass
class ControllerFragment:
    """Compile output for one controller project."""

    machine: Machine
    columns: list[Column] = field(default_factory=list)
    appliances: list[Appliance] = field(default_factory=list)
    bindings: list[DriveBinding] = field(default_factory=list)
    codelines: list[Codeline] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    source_path: str = ""
    source_sha256: str = ""
