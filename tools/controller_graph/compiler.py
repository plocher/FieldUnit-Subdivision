"""Compile a controller-project netlist into a ControllerFragment."""

from __future__ import annotations

import hashlib
from pathlib import Path

from kicad_services.types import NetlistComponent, NetlistModel

import re

from controller_graph.types import (
    Appliance,
    Codeline,
    Column,
    ControllerFragment,
    Diagnostic,
    DriveBinding,
    Machine,
)

# Transport parameters exported on CODELINE symbols (design doc §4).
_CODELINE_PARAMS = ("Broker", "TopicRoot", "Topic", "Port", "Baud")

# PANEL is the operator-interface Role (FieldUnit ADR 0003 D8). APPLIANCE is its
# pre-ADR spelling, still in the frozen desk golden; accepted until that changes.
_PANEL_ROLES = ("PANEL", "APPLIANCE")
_ROLES = ("MACHINE", "COLUMN", *_PANEL_ROLES, "IODRIVER", "CODELINE")
_APPLIANCE_KINDS = (
    "SWITCH_LEVER",
    "LOCK_LEVER",
    "LOCK_LEVER_2LAMP_2CONTACT",
    "SIGNAL_LEVER",
    "LAMP",
    "CODE",
    "MAINTAINER_CALL",
    "AUXILIARY",
)
_TRANSPORTS = ("VIRTUAL", "MQTT", "CMRInet")

# Bit numbers carry meaning only on IODRIVER pins: A1..A8 are bits 0..7 and
# B1..B8 bits 8..15 (ADR 0003 driver convention); bit<N> is the pre-ADR
# spelling still in the frozen desk golden.
_BIT_PIN = re.compile(r"^(?:bit(\d+)|([AB])([1-8]))$")


def _driver_bit(pinfunction: str) -> int | None:
    """Chip bit of an IODRIVER pin, or None when the pin is not a bit."""
    match = _BIT_PIN.match(_pin_function(pinfunction))
    if not match:
        return None
    if match.group(1) is not None:
        return int(match.group(1))
    return (0 if match.group(2) == "A" else 8) + int(match.group(3)) - 1


def _is_lock_lever(kind: str) -> bool:
    """LOCK_LEVER and its variants (pin sets differ, the family is one)."""
    return kind == "LOCK_LEVER" or kind.startswith("LOCK_LEVER_")


def _pin_function(pinfunction: str) -> str:
    """Function name from a netlist pinfunction like 'NWS_2' or 'Column_1'."""
    return pinfunction.rsplit("_", 1)[0]


# A pin named ~{X} (KiCad overbar) is function X, asserted-low (ADR 0003 D6).
_ASSERTED_LOW = re.compile(r"^~\{(.+)\}$")


def _function_polarity(pinfunction: str) -> tuple[str, bool]:
    """(function, active_low) from a pinfunction like '~{NWS}_2'."""
    name = _pin_function(pinfunction)
    match = _ASSERTED_LOW.match(name)
    return (match.group(1), True) if match else (name, False)


def _tokens(comp: NetlistComponent, field_name: str) -> tuple[str, ...]:
    """Parse a comma-separated token field; empty field means no tokens."""
    raw = comp.fields.get(field_name, "")
    return tuple(t.strip() for t in raw.split(",") if t.strip())


def _root_sheet_error(comp: NetlistComponent) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="root-sheet-symbol",
        subject=comp.reference,
        message=(
            f"{comp.reference} ({comp.value}) sits on the root sheet; "
            "COLUMN and CODELINE symbols belong on interlocking sheets"
        ),
    )


def _sheet_name(component: NetlistComponent) -> str:
    """Interlocking name from the component's sheet path ('/Luchessa/')."""
    return component.sheetpath.strip("/")


def compile_controller(netlist: NetlistModel) -> ControllerFragment:
    """Compile one controller project's netlist into a fragment."""
    diagnostics: list[Diagnostic] = []
    if netlist.components and not netlist.nets:
        # A broken root-sheet UUID exports exactly this, and ERC misses it.
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="netlist-no-nets",
                subject=str(netlist.path),
                message=(
                    "netlist has components but zero nets; the sheet "
                    "hierarchy is broken (root sheet UUID mismatch?)"
                ),
            )
        )

    # Every symbol declares its role in fields, never in its name.
    for comp in netlist.components.values():
        role = comp.fields.get("Role", "")
        if not role:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="missing-role",
                    subject=comp.reference,
                    message=f"{comp.reference} ({comp.value}) has no Role field",
                )
            )
        elif role not in _ROLES:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="unknown-role",
                    subject=comp.reference,
                    message=f"{comp.reference} has unknown Role {role!r}",
                )
            )
        elif role in _PANEL_ROLES:
            kind = comp.fields.get("Kind", "")
            if kind not in _APPLIANCE_KINDS:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="unknown-kind",
                        subject=comp.reference,
                        message=(
                            f"appliance {comp.reference} has unknown Kind "
                            f"{kind!r}"
                        ),
                    )
                )
            elif kind == "LAMP" and not _tokens(comp, "IndicationToken"):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="lamp-no-tokens",
                        subject=comp.reference,
                        message=(
                            f"lamp {comp.reference} has an empty "
                            "IndicationToken; every lamp lists the "
                            "indications OR'd onto it"
                        ),
                    )
                )

    machine = Machine(name="", machine_type="", columns=0)
    machine_count = 0
    columns: list[Column] = []
    column_by_ref: dict[str, Column] = {}
    appliance_refs: list[NetlistComponent] = []

    for comp in netlist.components.values():
        role = comp.fields.get("Role", "")
        if role == "MACHINE":
            machine_count += 1
            raw_columns = comp.fields.get("Columns", "0") or "0"
            if not raw_columns.isdigit():
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="machine-columns-invalid",
                        subject=comp.reference,
                        message=(
                            f"machine {comp.value!r} Columns "
                            f"{raw_columns!r} is not a number"
                        ),
                    )
                )
                raw_columns = "0"
            machine = Machine(
                name=comp.value,
                machine_type=comp.fields.get("Type", ""),
                columns=int(raw_columns),
            )
        elif role == "COLUMN":
            if not _sheet_name(comp):
                diagnostics.append(_root_sheet_error(comp))
                continue
            if not comp.value.isdigit():
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="column-number-invalid",
                        subject=comp.reference,
                        message=(
                            f"column {comp.reference} Value {comp.value!r} "
                            "is not a column number"
                        ),
                    )
                )
                continue
            column = Column(
                number=int(comp.value),
                cp_name=comp.fields.get("CP Name", ""),
                interlocking=_sheet_name(comp),
            )
            columns.append(column)
            column_by_ref[comp.reference] = column
        elif role in _PANEL_ROLES:
            appliance_refs.append(comp)

    if machine_count != 1:
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="machine-count",
                subject=str(netlist.path),
                message=(
                    f"controller project has {machine_count} MACHINE "
                    "symbols; it needs exactly one"
                ),
            )
        )

    numbers_seen: dict[int, Column] = {}
    for column in columns:
        first = numbers_seen.setdefault(column.number, column)
        if first is not column:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="column-number-duplicate",
                    subject=str(column.number),
                    message=(
                        f"column number {column.number} is used on both "
                        f"sheet {first.interlocking} and sheet "
                        f"{column.interlocking}; column numbers are "
                        "machine-wide"
                    ),
                )
            )

    codelines: list[Codeline] = []
    sheets_with_columns = {c.interlocking for c in columns}
    for comp in netlist.components.values():
        if comp.fields.get("Role", "") != "CODELINE":
            continue
        sheet = _sheet_name(comp)
        if not sheet:
            diagnostics.append(_root_sheet_error(comp))
            continue
        station = comp.fields.get("Station", "")
        if comp.value not in _TRANSPORTS:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="codeline-unknown-transport",
                    subject=comp.reference,
                    message=(
                        f"codeline {comp.reference} on sheet {sheet} has "
                        f"unknown transport {comp.value!r}"
                    ),
                )
            )
        elif comp.value == "CMRInet" and not (
            station.isdigit() and 0 <= int(station) <= 127
        ):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="codeline-bad-station",
                    subject=comp.reference,
                    message=(
                        f"CMRInet Station {station!r} on sheet {sheet} is "
                        "not a node UA from 0 to 127"
                    ),
                )
            )
        elif comp.value == "MQTT" and any(c in station for c in "/+#"):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="codeline-bad-station",
                    subject=comp.reference,
                    message=(
                        f"MQTT Station {station!r} on sheet {sheet} contains "
                        "a topic metacharacter (/ + #)"
                    ),
                )
            )
        codelines.append(
            Codeline(
                interlocking=sheet,
                transport=comp.value,
                station=station,
                stub=sheet not in sheets_with_columns,
                params={
                    key: comp.fields[key]
                    for key in _CODELINE_PARAMS
                    if comp.fields.get(key)
                },
            )
        )

    # A really empty sheet (no components, not even a codeline symbol)
    # still names an interlocking: fill in a defaulted VIRTUAL codeline.
    occupied_sheets = {
        _sheet_name(comp) for comp in netlist.components.values()
    }
    codeline_sheet_names = {c.interlocking for c in codelines}
    for sheet_path in netlist.sheets:
        sheet = sheet_path.strip("/")
        if not sheet or sheet in occupied_sheets:
            continue
        if sheet in codeline_sheet_names:
            continue
        codelines.append(
            Codeline(
                interlocking=sheet,
                transport="VIRTUAL",
                station=sheet,
                stub=True,
                defaulted=True,
            )
        )
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="sheet-empty-defaulted",
                subject=sheet,
                message=(
                    f"sheet {sheet} is empty; defaulted to a VIRTUAL "
                    f"codeline with station {sheet!r} (TBD placeholder)"
                ),
            )
        )

    drivers = {
        comp.reference: comp
        for comp in netlist.components.values()
        if comp.fields.get("Role", "") == "IODRIVER"
    }
    appliance_by_ref = {comp.reference: comp for comp in appliance_refs}

    # Membership: a net joining an appliance's Column pin to a COLUMN pin.
    # Drive bits: a net joining an appliance function pin to a driver bit pin.
    appliance_columns: dict[str, set[int]] = {}
    column_by_number = {c.number: c for c in columns}
    bindings: list[DriveBinding] = []
    for net in netlist.nets:
        net_columns: list[Column] = []
        members: list[str] = []
        driver_bits: list[tuple[NetlistComponent, int]] = []
        functions: list[tuple[str, str, bool]] = []
        for node in net.nodes:
            if node.reference in column_by_ref:
                net_columns.append(column_by_ref[node.reference])
            elif node.reference in drivers:
                bit = _driver_bit(node.pinfunction)
                if bit is not None:
                    driver_bits.append((drivers[node.reference], bit))
            elif node.reference in appliance_by_ref:
                function, active_low = _function_polarity(node.pinfunction)
                if function == "Column":
                    members.append(node.reference)
                else:
                    functions.append((node.reference, function, active_low))
        for ref in members:
            appliance_columns.setdefault(ref, set()).update(
                c.number for c in net_columns
            )
        if len(driver_bits) > 1:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="net-multiple-driver-bits",
                    subject=net.name,
                    message=(
                        f"net {net.name!r} touches "
                        f"{len(driver_bits)} IODRIVER bit pins; a "
                        "binding must name exactly one bit"
                    ),
                )
            )
        elif len(driver_bits) == 1:
            driver, bit = driver_bits[0]
            for ref, function, active_low in functions:
                bindings.append(
                    DriveBinding(
                        appliance=ref,
                        function=function,
                        driver=driver.value,
                        bus_kind=driver.fields.get("BusKind", ""),
                        bit=bit,
                        active_low=active_low,
                    )
                )
        else:
            for ref, function, _ in functions:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="function-unbound",
                        subject=ref,
                        message=(
                            f"appliance function pin {function} of {ref} is "
                            "not wired to any IODRIVER bit"
                        ),
                    )
                )

    # One driver bit drives one appliance function.
    by_bit: dict[tuple[str, int], list[DriveBinding]] = {}
    for binding in bindings:
        by_bit.setdefault((binding.driver, binding.bit), []).append(binding)
    for (driver_value, bit), shared in sorted(by_bit.items()):
        if len(shared) > 1:
            users = ", ".join(
                f"{b.appliance}.{b.function}" for b in shared
            )
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="driver-bit-shared",
                    subject=driver_value,
                    message=(
                        f"driver {driver_value} bit {bit} is used by "
                        f"{users}"
                    ),
                )
            )

    appliances = []
    if netlist.nets:
        for comp in appliance_refs:
            numbers = appliance_columns.get(comp.reference, set())
            if not numbers:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="appliance-no-column",
                        subject=comp.reference,
                        message=(
                            f"appliance {comp.value} ({comp.reference}) has "
                            "no column"
                        ),
                    )
                )
                continue
            if len(numbers) > 1:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="appliance-multiple-columns",
                        subject=comp.reference,
                        message=(
                            f"appliance {comp.value} ({comp.reference}) is "
                            f"wired to columns {sorted(numbers)}"
                        ),
                    )
                )
                continue
            column = column_by_number[numbers.pop()]
            appliances.append(
                Appliance(
                    reference=comp.reference,
                    kind=comp.fields.get("Kind", ""),
                    name=comp.value,
                    column=column.number,
                    interlocking=column.interlocking,
                    indication_tokens=_tokens(comp, "IndicationToken"),
                    control_tokens=_tokens(comp, "ControlToken"),
                )
            )

    # Column rules: a column IS a CP. At most one switch or lock lever, at
    # most one signal lever, at least one of them; CP Name must be real.
    for column in columns:
        cp_name = column.cp_name.strip()
        if not cp_name or cp_name.lower() == "cp name":
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="cp-name-unset",
                    subject=str(column.number),
                    message=(
                        f"column {column.number} has no CP Name (empty or "
                        "library placeholder)"
                    ),
                )
            )
    if netlist.nets:
        for column in columns:
            on_column = [a for a in appliances if a.column == column.number]
            switch_levers = [
                a
                for a in on_column
                if a.kind == "SWITCH_LEVER" or _is_lock_lever(a.kind)
            ]
            signal_levers = [a for a in on_column if a.kind == "SIGNAL_LEVER"]
            if (
                len(switch_levers) > 1
                or len(signal_levers) > 1
                or not (switch_levers or signal_levers)
            ):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="column-lever-rule",
                        subject=str(column.number),
                        message=(
                            f"column {column.number} has "
                            f"{len(switch_levers)} switch/lock and "
                            f"{len(signal_levers)} signal levers; a column "
                            "takes at most one of each and at least one"
                        ),
                    )
                )

    # Sheet rules: a drawn interlocking sheet (one with columns) has exactly
    # one CODE button and exactly one CODELINE. Stub sheets are exempt from
    # the CODE rule by definition.
    if netlist.nets:
        for sheet in sorted(sheets_with_columns):
            codes_on_sheet = [
                a
                for a in appliances
                if a.interlocking == sheet and a.kind == "CODE"
            ]
            if len(codes_on_sheet) != 1:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="sheet-code-count",
                        subject=sheet,
                        message=(
                            f"interlocking sheet {sheet} has "
                            f"{len(codes_on_sheet)} CODE buttons; it needs "
                            "exactly one"
                        ),
                    )
                )
    codeline_sheets = [c.interlocking for c in codelines]
    for sheet in sorted(
        sheets_with_columns.union(codeline_sheets) - {""}
    ):
        count = codeline_sheets.count(sheet)
        if count != 1:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="sheet-codeline-count",
                    subject=sheet,
                    message=(
                        f"interlocking sheet {sheet} has {count} CODELINE "
                        "symbols; it needs exactly one"
                    ),
                )
            )

    columns.sort(key=lambda c: c.number)
    appliances.sort(key=lambda a: (a.column, a.kind, a.name))
    source_sha256 = ""
    try:
        source_sha256 = hashlib.sha256(
            Path(netlist.path).read_bytes()
        ).hexdigest()
    except OSError:
        pass

    bindings.sort(key=lambda b: (b.driver, b.bit))
    codelines.sort(key=lambda c: c.interlocking)
    return ControllerFragment(
        source_path=str(netlist.path),
        source_sha256=source_sha256,
        machine=machine,
        columns=columns,
        appliances=appliances,
        bindings=bindings,
        codelines=codelines,
        diagnostics=diagnostics,
    )
