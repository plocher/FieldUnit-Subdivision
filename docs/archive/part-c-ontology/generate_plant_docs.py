#!/usr/bin/env python3
"""Generate an offline HTML documentation packet for one plant source document."""

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class SourceDocument:
    """The source information required to create a single-plant packet."""

    name: str
    path: Path
    plant: JsonObject
    diagram: JsonObject | None


@dataclass(frozen=True)
class HistoricalPlant:
    """Structured information recovered from one historical XML definition."""

    name: str
    path: Path
    document_text: str
    raw_xml: str
    inventories: dict[str, set[str]]
    detector_locks: set[tuple[str, str]]


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    """Parse the supported single-plant command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate an offline HTML packet for one Interlocking Plant source document."
    )
    parser.add_argument(
        "plant",
        help="Source document path or path stem; '.json' is optional.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML path. Defaults to the source path with a .html suffix.",
    )
    parser.add_argument(
        "--historical-xml",
        type=Path,
        help="Informational historical XML source for a reconciliation packet.",
    )
    parser.add_argument(
        "--historical-pdf",
        type=Path,
        help="Optional historical engineering PDF embedded in the reconciliation packet.",
    )
    return parser.parse_args(arguments)


def resolve_source_path(argument: str) -> Path:
    """Resolve a positional source-document path with an optional JSON suffix."""
    path = Path(argument)
    if path.suffix == ".json":
        return path
    return path.with_suffix(".json")


def as_object(value: Any, context: str) -> JsonObject:
    """Return a JSON object or raise a useful validation error."""
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a JSON object.")
    return value


def as_object_list(value: Any, context: str) -> list[JsonObject]:
    """Return a JSON object list or raise a useful validation error."""
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{context} must be a list of JSON objects.")
    return [as_object(item, context) for item in value]


def load_source_document(path: Path) -> SourceDocument:
    """Load a source document and extract its embedded track diagram."""
    try:
        raw_document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Source document does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Source document is not valid JSON: {error}") from error

    plant = as_object(raw_document, "Source document")
    name = plant.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("Source document requires a non-empty 'name'.")

    design_value = plant.get("design")
    design = design_value if isinstance(design_value, dict) else {}
    diagram_value = design.get("diagram")
    diagram = diagram_value if isinstance(diagram_value, dict) else None
    return SourceDocument(name=name, path=path, plant=plant, diagram=diagram)

def load_historical_plant(path: Path) -> HistoricalPlant:
    """Load a historical XML definition as informational reconciliation evidence."""
    try:
        raw_xml = path.read_text(encoding="utf-8")
        root = element_tree.fromstring(raw_xml)
    except FileNotFoundError as error:
        raise ValueError(f"Historical XML does not exist: {path}") from error
    except element_tree.ParseError as error:
        raise ValueError(f"Historical XML is not well-formed: {error}") from error

    name = root.get("name")
    if root.tag != "controlpoint" or not name:
        raise ValueError("Historical XML requires a controlpoint root with a name.")

    inventories = {
        "Track circuits": {
            value
            for element in root.findall("./trackcircuits/trackcircuit")
            if (value := element.get("name"))
        },
        "Switches": {
            value
            for element in root.findall("./switches/switch")
            if (value := element.get("name"))
        },
        "Signal heads": {
            value
            for element in root.findall("./signals/signal/head")
            if (value := element.get("name"))
        },
        "Routes": {
            value
            for element in root.findall("./signals/signal/head/route")
            if (value := element.get("name"))
        },
        "Controls": {
            value
            for element in root.findall("./controls/control")
            if (value := element.get("name"))
        },
        "Indications": {
            value
            for element in root.findall("./indications/indication")
            if (value := element.get("name"))
        },
    }
    document_text = root.findtext("./doc", default="").strip()
    detector_locks = {
        (switch_name, track_circuit)
        for element in root.findall("./switches/switch")
        if (switch_name := element.get("name"))
        and (track_circuit := element.get("trackcircuit"))
    }
    return HistoricalPlant(
        name=name,
        path=path,
        document_text=document_text,
        raw_xml=raw_xml,
        inventories=inventories,
        detector_locks=detector_locks,
    )


def collect_source_inventories(plant: JsonObject) -> dict[str, set[str]]:
    """Collect current source-document inventories for reconciliation."""
    mapping = {
        "Track circuits": "trackCircuits",
        "Switches": "switches",
        "Signal heads": "signalMasts",
        "Routes": "routes",
    }
    inventories: dict[str, set[str]] = {}
    for label, member_name in mapping.items():
        inventories[label] = {
            item["name"]
            for item in as_object_list(plant.get(member_name, []), member_name)
            if isinstance(item.get("name"), str)
        }
    inventories["Controls"] = set()
    inventories["Indications"] = set()
    return inventories


def collect_source_detector_locks(plant: JsonObject) -> set[tuple[str, str]]:
    """Collect declared detector-lock pairs from a current source document."""
    return {
        (switch_name, track_circuit)
        for item in as_object_list(plant.get("detectorLocks", []), "detectorLocks")
        if (switch_name := item.get("switch"))
        and (track_circuit := item.get("trackCircuit"))
        and isinstance(switch_name, str)
        and isinstance(track_circuit, str)
    }


def collect_named_entities(plant: JsonObject) -> dict[str, set[str]]:
    """Collect plant-local vital identities for diagram-reference validation."""
    entity_keys = {
        "trackCircuit": "trackCircuits",
        "switch": "switches",
        "crossover": "crossovers",
        "signalMast": "signalMasts",
        "signalRoute": "routes",
    }
    entities: dict[str, set[str]] = {}
    for reference_kind, plant_key in entity_keys.items():
        values = plant.get(plant_key, [])
        if not isinstance(values, list):
            raise ValueError(f"Plant member '{plant_key}' must be an array when present.")
        names = {
            item["name"]
            for item in as_object_list(values, f"Plant member '{plant_key}'")
            if isinstance(item.get("name"), str)
        }
        entities[reference_kind] = names
    entities["interlockingPlant"] = {plant["name"]}
    return entities


def validate_diagram(document: SourceDocument) -> list[str]:
    """Validate source-document references required by the first packet slice."""
    errors: list[str] = []
    diagram = document.diagram
    if diagram is None:
        return ["Source document 'design.diagram' must be a JSON object."]
    if diagram.get("kind") != "track-diagram":
        errors.append("design.diagram.kind must be 'track-diagram'.")

    subject = diagram.get("subject")
    if not isinstance(subject, dict) or subject.get("kind") != "interlockingPlant":
        errors.append("design.diagram.subject must reference an interlockingPlant.")
    elif subject.get("id") != document.name:
        errors.append(
            "design.diagram.subject.id must match the source document plant name."
        )

    sheets = diagram.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        errors.append("design.diagram.sheets must contain at least one sheet.")
        return errors

    entities = collect_named_entities(document.plant)
    for sheet in as_object_list(sheets, "design.diagram.sheets"):
        sheet_id = sheet.get("id", "<unknown sheet>")
        elements = as_object_list(sheet.get("nodes", []), f"Sheet '{sheet_id}' nodes")
        elements += as_object_list(
            sheet.get("junctions", []), f"Sheet '{sheet_id}' junctions"
        )
        element_ports = {
            element.get("id"): {
                port.get("id")
                for port in as_object_list(
                    element.get("ports", []), f"Sheet '{sheet_id}' element ports"
                )
            }
            for element in elements
            if isinstance(element.get("id"), str)
        }

        for segment in as_object_list(
            sheet.get("segments", []), f"Sheet '{sheet_id}' segments"
        ):
            for endpoint_name in ("from", "to"):
                endpoint = segment.get(endpoint_name)
                if not isinstance(endpoint, dict):
                    errors.append(
                        f"Segment '{segment.get('id')}' has no '{endpoint_name}' port."
                    )
                    continue
                element_id = endpoint.get("elementId")
                port_id = endpoint.get("portId")
                if element_id not in element_ports or port_id not in element_ports.get(
                    element_id, set()
                ):
                    errors.append(
                        f"Segment '{segment.get('id')}' references unknown "
                        f"{endpoint_name} port '{element_id}.{port_id}'."
                    )

        for element in [
            *elements,
            *as_object_list(sheet.get("segments", []), f"Sheet '{sheet_id}' segments"),
            *as_object_list(sheet.get("overlays", []), f"Sheet '{sheet_id}' overlays"),
        ]:
            for reference in as_object_list(
                element.get("refs", []), f"Sheet '{sheet_id}' element references"
            ):
                reference_kind = reference.get("kind")
                reference_id = reference.get("id")
                if (
                    reference_kind in entities
                    and reference_id not in entities[reference_kind]
                ):
                    errors.append(
                        f"Element '{element.get('id')}' references unknown "
                        f"{reference_kind} '{reference_id}'."
                    )
    return errors


def position_for_element(element: JsonObject) -> tuple[float, float]:
    """Extract a diagram element's canvas position."""
    position = as_object(element.get("position"), f"Element '{element.get('id')}' position")
    x = position.get("x")
    y = position.get("y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError(f"Element '{element.get('id')}' position requires numeric x and y.")
    return float(x), float(y)


def render_diagram(diagram: JsonObject) -> str:
    """Render all diagram sheets as embedded SVG."""
    rendered_sheets: list[str] = []
    for sheet in as_object_list(diagram["sheets"], "design.diagram.sheets"):
        nodes = as_object_list(sheet["nodes"], f"Sheet '{sheet['id']}' nodes")
        junctions = as_object_list(sheet["junctions"], f"Sheet '{sheet['id']}' junctions")
        positions = {
            str(element["id"]): position_for_element(element)
            for element in [*nodes, *junctions]
        }
        svg_parts = [
            f'<section class="diagram-sheet"><h3>{html.escape(str(sheet["name"]))}</h3>',
            '<svg class="track-diagram" viewBox="0 0 320 120" role="img">',
        ]
        for segment in as_object_list(sheet["segments"], f"Sheet '{sheet['id']}' segments"):
            start = positions[str(segment["from"]["elementId"])]
            end = positions[str(segment["to"]["elementId"])]
            style = as_object(segment.get("style", {}), "Segment style")
            css_class = html.escape(
                f'{style.get("trackClass", "side")} {style.get("stroke", "solid")}'
            )
            svg_parts.append(
                f'<line class="{css_class}" data-diagram-id="{html.escape(str(segment["id"]))}" '
                f'x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" />'
            )
        for node in nodes:
            x, y = position_for_element(node)
            svg_parts.append(
                f'<circle class="diagram-node" cx="{x}" cy="{y}" r="4" '
                f'data-diagram-id="{html.escape(str(node["id"]))}" />'
            )
        for junction in junctions:
            x, y = position_for_element(junction)
            svg_parts.append(
                f'<rect class="diagram-junction" x="{x - 4}" y="{y - 4}" width="8" '
                f'height="8" data-diagram-id="{html.escape(str(junction["id"]))}" />'
            )
        for overlay in as_object_list(sheet["overlays"], f"Sheet '{sheet['id']}' overlays"):
            x, y = position_for_element(overlay)
            text = html.escape(str(overlay.get("text", "")))
            svg_parts.append(f'<text x="{x}" y="{y}">{text}</text>')
        svg_parts.append("</svg></section>")
        rendered_sheets.append("\n".join(svg_parts))
    return "\n".join(rendered_sheets)


def render_rows(rows: list[list[str]]) -> str:
    """Render HTML table rows from already escaped cell text."""
    return "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )


def render_switch_alignment(route: JsonObject) -> str:
    """Render Switch alignments as Normal names and parenthesized Reverse names."""
    alignments = as_object_list(route.get("aligns", []), "Route aligns")
    return "".join(
        f"({alignment.get('switch')})"
        if alignment.get("position") == "REVERSE"
        else f"\N{NO-BREAK SPACE}{alignment.get('switch', '')}\N{NO-BREAK SPACE}"
        for alignment in alignments
    )

def render_route_table(plant: JsonObject) -> str:
    """Render the declared vital signal routes without inferring any new routes."""
    rows: list[list[str]] = []
    for route in as_object_list(plant.get("routes", []), "Plant routes"):
        displays = as_object(route.get("displays", {}), "Route displays")
        rows.append(
            [
                str(route.get("name", "")),
                str(displays.get("mast", "")),
                render_switch_alignment(route),
                ", ".join(str(block) for block in route.get("clears", [])),
                str(displays.get("maxIndication", "")),
            ]
        )
    headers = (
        "<tr><th>Route</th><th>Signal mast</th><th>Switch alignment</th>"
        "<th>Required clear blocks</th><th>Indication</th></tr>"
    )
    return f'<table class="route-table"><thead>{headers}</thead><tbody>{render_rows(rows)}</tbody></table>'


def render_detector_locks(plant: JsonObject) -> str:
    """Render declared detector-lock couplings."""
    rows = [
        [str(lock.get("switch", "")), str(lock.get("trackCircuit", ""))]
        for lock in as_object_list(plant.get("detectorLocks", []), "Plant detectorLocks")
    ]
    return (
        "<table><thead><tr><th>Switch</th><th>Track circuit</th></tr></thead>"
        f"<tbody>{render_rows(rows)}</tbody></table>"
    )


def build_packet(document: SourceDocument) -> str:
    """Build one self-contained offline HTML packet."""
    if document.diagram is None:
        raise ValueError("A complete packet requires design.diagram.")
    title = html.escape(f"{document.name} — Plant Documentation")
    diagram_html = render_diagram(document.diagram)
    route_table = render_route_table(document.plant)
    detector_locks = render_detector_locks(document.plant)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ background: #f5f3ed; color: #1d2830; font: 16px system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; }}
h1, h2, h3 {{ color: #193a52; }}
section {{ background: white; border: 1px solid #c6c3b9; border-radius: .4rem; margin: 1rem 0; padding: 1rem; }}
.track-diagram {{ background: #fbfaf5; border: 1px solid #d0cdc0; max-width: 100%; }}
.track-diagram line {{ stroke: #263d4d; stroke-width: 4; }}
.track-diagram line.mainline {{ stroke-width: 6; }}
.track-diagram line.dashed {{ stroke-dasharray: 8 5; }}
.diagram-node {{ fill: #193a52; }}
.diagram-junction {{ fill: #b05435; }}
.track-diagram text {{ fill: #1d2830; font-size: 10px; text-anchor: middle; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #c6c3b9; padding: .45rem; text-align: left; vertical-align: top; }}
th {{ background: #e3edf1; }}
.incomplete {{ color: #8a3b22; font-weight: 600; }}
.route-table {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
.route-table td, .route-table th {{ white-space: nowrap; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>Source document: <code>{html.escape(str(document.path))}</code></p>
<section><h2>Track diagram</h2>{diagram_html}</section>
<section><h2>Interlocking control table</h2>{route_table}</section>
<section><h2>Detector locks</h2>{detector_locks}</section>
<section><h2>CodeLine wire ledger</h2><p class="incomplete">No CodeLine ledger is declared in this source document.</p></section>
</body>
</html>
"""


def render_reconciliation_rows(
    source_inventories: dict[str, set[str]],
    historical_inventories: dict[str, set[str]],
) -> str:
    """Render a source-versus-history inventory comparison table."""
    rows: list[list[str]] = []
    for label in historical_inventories:
        historical_values = historical_inventories[label]
        source_values = source_inventories.get(label, set())
        rows.append(
            [
                label,
                ", ".join(sorted(historical_values - source_values)) or "—",
                ", ".join(sorted(source_values & historical_values)) or "—",
                ", ".join(sorted(source_values - historical_values)) or "—",
            ]
        )
    headings = (
        "<tr><th>Category</th><th>Historical only</th><th>Common</th>"
        "<th>Current source only</th></tr>"
    )
    return f"<table><thead>{headings}</thead><tbody>{render_rows(rows)}</tbody></table>"

def render_office_sketch(presentation: JsonObject) -> str:
    """Render a concise cTc station sketch from informational source data."""
    office_sketch = as_object(
        presentation.get("officeSketch"), "design.historicalPresentation.officeSketch"
    )
    station = office_sketch.get("station")
    if not isinstance(station, str) or not station:
        raise ValueError("design.historicalPresentation.officeSketch requires a station.")

    lines = [f'machine.addStation("{station}")']
    for column in as_object_list(office_sketch.get("columns", []), "officeSketch columns"):
        number = column.get("number")
        if not isinstance(number, int):
            raise ValueError("officeSketch column requires an integer number.")
        line = f"      .inColumn({number})"
        if isinstance(column.get("switch"), str):
            switch_name = column.get("switchName")
            nameplate = column.get("nameplate", "SWITCH")
            arguments = [f'"{column["switch"]}"']
            if isinstance(switch_name, str):
                arguments.append(f'"{switch_name}"')
            if isinstance(nameplate, str):
                arguments.append(f'"{nameplate}"')
            line += f".withSwitch({', '.join(arguments)})"
        if isinstance(column.get("signal"), str):
            signal_name = column.get("signalName")
            arguments = [f'"{column["signal"]}"']
            if isinstance(signal_name, str):
                arguments.append(f'"{signal_name}"')
            line += f".withSignal({', '.join(arguments)})"
        track_lamps = column.get("trackLamps", [])
        if track_lamps:
            if not isinstance(track_lamps, list) or not all(
                isinstance(track_name, str) for track_name in track_lamps
            ):
                raise ValueError("officeSketch trackLamps must contain strings.")
            lamps = ", ".join(f'"{track_name}"' for track_name in track_lamps)
            line += f".withTrackLamps({{ {lamps} }})"
        if isinstance(column.get("maintainerCall"), str):
            line += f'.withMaintainerCall("{column["maintainerCall"]}")'
        if column.get("codeButton") is True:
            line += ".withCodeButton()"
        lines.append(line)
    return html.escape("\n".join(lines) + ";")


def render_historical_route_table(presentation: JsonObject) -> str:
    """Render the informational route table in signal-head-oriented form."""
    entries = as_object_list(
        presentation.get("routeTable", []), "design.historicalPresentation.routeTable"
    )
    lines: list[str] = []
    for entry in entries:
        mast = entry.get("mast")
        alignment = entry.get("alignment")
        if not isinstance(mast, str) or not isinstance(alignment, str):
            raise ValueError("Each historical route entry requires mast and alignment.")
        lines.append(mast)
        heads = as_object_list(entry.get("heads", []), f"Route entry '{mast}' heads")
        if not heads:
            requirements = entry.get("requirements", [])
            indication = entry.get("indication")
            if not isinstance(requirements, list) or not isinstance(indication, str):
                raise ValueError(
                    f"Route entry '{mast}' without heads requires requirements and indication."
                )
            lines.append(
                f"  {alignment:<10} {' '.join(map(str, requirements)):<38} {indication}"
            )
            continue
        for head in heads:
            head_name = head.get("name")
            requirements = head.get("requirements")
            indication = head.get("indication")
            if (
                not isinstance(head_name, str)
                or not isinstance(requirements, list)
                or not isinstance(indication, str)
            ):
                raise ValueError(
                    f"Route entry '{mast}' head requires name, requirements, and indication."
                )
            lines.append(
                f"  {alignment:<10} {head_name}: {' '.join(map(str, requirements)):<34} {indication}"
            )
        note = entry.get("note")
        if isinstance(note, str) and note:
            lines.append(f"              note: {note}")
    return html.escape("\n".join(lines))


def build_reconciliation_packet(
    document: SourceDocument,
    historical: HistoricalPlant,
) -> str:
    """Build an offline informational packet without changing the source candidate."""
    title = html.escape(f"{document.name} — Reconciliation Packet")
    comparison = render_reconciliation_rows(
        collect_source_inventories(document.plant), historical.inventories
    )
    source_locks = collect_source_detector_locks(document.plant)
    historical_locks = historical.detector_locks
    lock_rows = render_rows(
        [
            [
                ", ".join(
                    f"{switch_name} / {track_circuit}"
                    for switch_name, track_circuit in sorted(historical_locks - source_locks)
                )
                or "—",
                ", ".join(
                    f"{switch_name} / {track_circuit}"
                    for switch_name, track_circuit in sorted(historical_locks & source_locks)
                )
                or "—",
                ", ".join(
                    f"{switch_name} / {track_circuit}"
                    for switch_name, track_circuit in sorted(source_locks - historical_locks)
                )
                or "—",
            ]
        ]
    )
    historical_note = html.escape(historical.document_text or "No historical note found.")
    current_source = html.escape(json.dumps(document.plant, indent=2, sort_keys=True))
    historical_source = html.escape(historical.raw_xml)
    design = document.plant.get("design")
    presentation = (
        design.get("historicalPresentation") if isinstance(design, dict) else None
    )
    presentation_html = (
        "<p>No curated historical presentation is declared in this source document.</p>"
        if not isinstance(presentation, dict)
        else (
            '<pre class="office-sketch">'
            f"{render_office_sketch(presentation)}</pre>"
            '<pre class="route-table">'
            f"{render_historical_route_table(presentation)}</pre>"
        )
    )
    diagram_status = (
        "No track diagram was inferred from vital plant information."
        if document.diagram is None
        else "An embedded track diagram exists and remains subject to separate validation."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ background: #f5f3ed; color: #1d2830; font: 16px system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; }}
h1, h2 {{ color: #193a52; }}
section {{ background: white; border: 1px solid #c6c3b9; border-radius: .4rem; margin: 1rem 0; padding: 1rem; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #c6c3b9; padding: .45rem; text-align: left; vertical-align: top; }}
th {{ background: #e3edf1; }}
.informational {{ color: #5e4b1f; font-weight: 600; }}
code {{ overflow-wrap: anywhere; }}
pre {{ background: #fbfaf5; border: 1px solid #d0cdc0; overflow-x: auto; padding: 1rem; white-space: pre; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="informational">Historical XML is informational evidence. It does not alter the current source candidate or FieldUnit vital logic.</p>
<section>
<h2>Sources</h2>
<p>Current source: <code>{html.escape(str(document.path))}</code></p>
<p>Historical XML: <code>{html.escape(str(historical.path))}</code></p>
</section>
<section>
<h2>Historical plant note</h2>
<pre class="historical-note">{historical_note}</pre>
</section>
<section>
<h2>Informational operating sketch and route table</h2>
{presentation_html}
</section>
<section>
<h2>Source documents</h2>
<details>
<summary>Current source document</summary>
<pre>{current_source}</pre>
</details>
<details>
<summary>Historical XML source</summary>
<pre>{historical_source}</pre>
</details>
</section>
<section>
<h2>Structured inventory comparison</h2>
{comparison}
</section>
<section>
<h2>Detector locks</h2>
<table><thead><tr><th>Historical only</th><th>Common</th><th>Current source only</th></tr></thead><tbody>{lock_rows}</tbody></table>
</section>
<section>
<h2>Current design state</h2>
<p>{html.escape(diagram_status)}</p>
</section>
</body>
</html>
"""


def render_embedded_pdf(pdf_path: Path | None) -> str:
    """Embed historical PDF evidence without an external file dependency."""
    if pdf_path is None:
        return "<p>No historical engineering PDF was supplied.</p>"
    try:
        encoded_pdf = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    except FileNotFoundError as error:
        raise ValueError(f"Historical PDF does not exist: {pdf_path}") from error
    return (
        '<object class="historical-pdf" type="application/pdf" '
        f'data="data:application/pdf;base64,{encoded_pdf}">'
        "<p>The embedded historical PDF could not be displayed.</p></object>"
    )


def render_named_inventory(title: str, values: set[str]) -> str:
    """Render a concise table for one named source inventory."""
    rows = [[value] for value in sorted(values)] or [["—"]]
    return (
        f"<h3>{html.escape(title)}</h3>"
        f"<table><thead><tr><th>Name</th></tr></thead><tbody>{render_rows(rows)}</tbody></table>"
    )


def render_switch_inventory(
    title: str,
    switches: set[str],
    detector_locks: set[tuple[str, str]],
) -> str:
    """Render field Switch appliances and their declared detector-lock circuits."""
    rows = [
        [
            switch_name,
            ", ".join(
                track_circuit
                for locked_switch, track_circuit in sorted(detector_locks)
                if locked_switch == switch_name
            )
            or "—",
        ]
        for switch_name in sorted(switches)
    ] or [["—", "—"]]
    return (
        f"<h3>{html.escape(title)}</h3>"
        "<table><thead><tr><th>Field switch</th><th>Detector-lock circuit</th>"
        f"</tr></thead><tbody>{render_rows(rows)}</tbody></table>"
    )

def render_panel_columns(plant: JsonObject) -> str:
    """Render physical cTc panel labels separately from route identifiers."""
    supervision = plant.get("supervision")
    if not isinstance(supervision, dict):
        return "<p>No physical panel columns are declared.</p>"
    columns = as_object_list(supervision.get("panelColumns", []), "supervision.panelColumns")
    rows: list[list[str]] = []
    for column in columns:
        controls: list[str] = []
        if isinstance(column.get("switchId"), str):
            nameplate = column.get("nameplate", "SWITCH")
            controls.append(
                f'{nameplate} {column["switchId"]} ({column.get("switchName", "unlabeled")})'
            )
        if isinstance(column.get("signalId"), str):
            controls.append(
                f'Signal {column["signalId"]} ({column.get("signalName", "unlabeled")})'
            )
        elif isinstance(column.get("lockId"), str):
            controls.append(
                f'Switch {column["lockId"]} lock ({column.get("lockName", "unlabeled")})'
            )
        state = ""
        if isinstance(column.get("lockedPosition"), str):
            state = f'Locked = {column["lockedPosition"]}'
        if column.get("unlockedControl") == "local":
            state = f"{state}; Unlocked = local control".strip("; ")
        rows.append(
            [
                str(column.get("number", "")),
                ", ".join(controls) or "—",
                state or "—",
            ]
        )
    return (
        "<h3>Physical cTc panel columns</h3>"
        "<table><thead><tr><th>Column</th><th>Control label</th><th>Lock semantics</th>"
        f"</tr></thead><tbody>{render_rows(rows)}</tbody></table>"
    )


def render_combined_inventory(
    source_inventories: dict[str, set[str]],
    historical_inventories: dict[str, set[str]],
) -> str:
    """Render a red/green inventory comparison for direct review."""
    rows: list[str] = []
    for label, historical_values in historical_inventories.items():
        source_values = source_inventories.get(label, set())
        historical_only = ", ".join(sorted(historical_values - source_values)) or "—"
        common = ", ".join(sorted(historical_values & source_values)) or "—"
        current_only = ", ".join(sorted(source_values - historical_values)) or "—"
        rows.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f'<td class="diff-removed">{html.escape(historical_only)}</td>'
            f'<td class="diff-common">{html.escape(common)}</td>'
            f'<td class="diff-added">{html.escape(current_only)}</td>'
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Category</th><th>Historical only</th><th>Common</th>"
        "<th>Current source only</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )

def render_combined_detector_locks(
    source_locks: set[tuple[str, str]],
    historical_locks: set[tuple[str, str]],
) -> str:
    """Render color-coded historical and current detector-lock pairs."""
    def format_locks(locks: set[tuple[str, str]]) -> str:
        return ", ".join(
            f"{switch_name} / {track_circuit}"
            for switch_name, track_circuit in sorted(locks)
        ) or "—"

    return (
        "<h3>Detector locks</h3>"
        "<table><thead><tr><th>Historical only</th><th>Common</th>"
        "<th>Current source only</th></tr></thead><tbody><tr>"
        f'<td class="diff-removed">{html.escape(format_locks(historical_locks - source_locks))}</td>'
        f'<td class="diff-common">{html.escape(format_locks(historical_locks & source_locks))}</td>'
        f'<td class="diff-added">{html.escape(format_locks(source_locks - historical_locks))}</td>'
        "</tr></tbody></table>"
    )

def render_route_review_findings(design: JsonObject) -> str:
    """Render declared route findings without changing the route configuration."""
    review = design.get("review")
    if not isinstance(review, dict):
        return "<p>No route review findings are declared.</p>"
    findings = as_object_list(review.get("routeFindings", []), "design.review.routeFindings")
    rows = [
        [
            str(finding.get("route", "")),
            str(finding.get("disposition", "")),
            str(finding.get("reason", "")),
            str(finding.get("replacementRoute", "—")),
        ]
        for finding in findings
    ] or [["—", "—", "—", "—"]]
    return (
        "<h3>Route review findings</h3>"
        "<table><thead><tr><th>Route</th><th>Disposition</th><th>Reason</th>"
        f"<th>Replacement route</th></tr></thead><tbody>{render_rows(rows)}</tbody></table>"
    )

def build_tabbed_reconciliation_packet(
    document: SourceDocument,
    historical: HistoricalPlant,
    historical_pdf_path: Path | None,
) -> str:
    """Build a three-view packet for historical, current, and combined review."""
    title = html.escape(f"{document.name} — Reconciliation Packet")
    design = as_object(document.plant.get("design"), "Source document 'design'")
    presentation = as_object(
        design.get("historicalPresentation"),
        "Source document 'design.historicalPresentation'",
    )
    source_inventories = collect_source_inventories(document.plant)
    source_locks = collect_source_detector_locks(document.plant)
    historical_note = html.escape(historical.document_text or "No historical note found.")
    current_source = html.escape(json.dumps(document.plant, indent=2, sort_keys=True))
    historical_source = html.escape(historical.raw_xml)
    historical_switches = render_switch_inventory(
        "Historical field switches / turnouts and Detector locks",
        historical.inventories["Switches"],
        historical.detector_locks,
    )
    current_switches = render_switch_inventory(
        "Current field switches and Detector locks",
        source_inventories["Switches"],
        source_locks,
    )
    current_routes = render_route_table(document.plant)
    combined_inventory = render_combined_inventory(
        source_inventories, historical.inventories
    )
    combined_locks = render_combined_detector_locks(
        source_locks, historical.detector_locks
    )
    review_findings = render_route_review_findings(design)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ background: #f5f3ed; color: #1d2830; font: 16px system-ui, sans-serif; margin: 2rem auto; max-width: 1300px; padding: 0 1rem; }}
h1, h2, h3 {{ color: #193a52; }}
section {{ background: white; border: 1px solid #c6c3b9; border-radius: .4rem; margin: 1rem 0; padding: 1rem; }}
.tab-list {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }}
.tab-button {{ background: #e3edf1; border: 1px solid #597281; border-radius: .3rem; color: #193a52; cursor: pointer; font: inherit; padding: .5rem 1rem; }}
.tab-button[aria-selected="true"] {{ background: #193a52; color: white; }}
.tab-page[hidden] {{ display: none; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #c6c3b9; padding: .45rem; text-align: left; vertical-align: top; }}
th {{ background: #e3edf1; }}
pre {{ background: #fbfaf5; border: 1px solid #d0cdc0; overflow-x: auto; padding: 1rem; white-space: pre; }}
.historical-pdf {{ border: 1px solid #d0cdc0; height: 800px; width: 100%; }}
.informational {{ color: #5e4b1f; font-weight: 600; }}
.diff-removed {{ background: #fde7e3; color: #8a2116; }}
.diff-common {{ background: #e5f4e7; color: #1e6334; }}
.diff-added {{ background: #e6eff8; color: #174d76; }}
.route-table {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
.route-table td, .route-table th {{ white-space: nowrap; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="informational">Historical sources are informational evidence. They do not alter the current source candidate or FieldUnit vital logic.</p>
<nav class="tab-list" aria-label="Reconciliation views">
<button class="tab-button" data-tab="historical" aria-selected="true">Historical</button>
<button class="tab-button" data-tab="current" aria-selected="false">Current</button>
<button class="tab-button" data-tab="combined" aria-selected="false">Combined diff</button>
</nav>
<main>
<section class="tab-page" id="historical">
<h2>Historical engineering view</h2>
{render_embedded_pdf(historical_pdf_path)}
<h3>Historical plant note</h3>
<pre class="historical-note">{historical_note}</pre>
<h3>Historical operating sketch</h3>
<pre class="office-sketch">{render_office_sketch(presentation)}</pre>
<h3>Historical route table</h3>
<pre class="route-table">{render_historical_route_table(presentation)}</pre>
{historical_switches}
{render_named_inventory("Historical signal heads", historical.inventories["Signal heads"])}
</section>
<section class="tab-page" id="current" hidden>
<h2>Current source view</h2>
<p>The current source candidate is incomplete. No track diagram was inferred from vital plant information.</p>
{render_panel_columns(document.plant)}
{current_switches}
{render_named_inventory("Current track circuits", source_inventories["Track circuits"])}
{render_named_inventory("Current signal masts", source_inventories["Signal heads"])}
<h3>Current named routes</h3>
{current_routes}
</section>
<section class="tab-page" id="combined" hidden>
<h2>Combined red/green diff</h2>
<p>Red marks historical-only information; green marks common information; blue marks current-source-only information.</p>
{combined_inventory}
{combined_locks}
{review_findings}
<details>
<summary>Current source document</summary>
<pre>{current_source}</pre>
</details>
<details>
<summary>Historical XML source</summary>
<pre>{historical_source}</pre>
</details>
</section>
</main>
<script>
for (const button of document.querySelectorAll(".tab-button")) {{
  button.addEventListener("click", () => {{
    for (const page of document.querySelectorAll(".tab-page")) {{
      page.hidden = page.id !== button.dataset.tab;
    }}
    for (const candidate of document.querySelectorAll(".tab-button")) {{
      candidate.setAttribute("aria-selected", String(candidate === button));
    }}
  }});
}}
</script>
</body>
</html>
"""


def build_incomplete_packet(document: SourceDocument, errors: list[str]) -> str:
    """Build an offline report for a source document that needs more design data."""
    title = html.escape(f"{document.name} — Incomplete Plant Documentation")
    error_items = "\n".join(f"<li>{html.escape(error)}</li>" for error in errors)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ background: #f5f3ed; color: #1d2830; font: 16px system-ui, sans-serif; margin: 2rem auto; max-width: 900px; padding: 0 1rem; }}
h1, h2 {{ color: #193a52; }}
section {{ background: white; border: 1px solid #c6c3b9; border-radius: .4rem; margin: 1rem 0; padding: 1rem; }}
.incomplete {{ color: #8a3b22; font-weight: 600; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>Source document: <code>{html.escape(str(document.path))}</code></p>
<section>
<h2>Incomplete design data</h2>
<p class="incomplete">No track diagram was inferred from vital plant information.</p>
<ul>{error_items}</ul>
</section>
</body>
</html>
"""


def main(arguments: list[str]) -> int:
    """Execute the single-plant packet command."""
    try:
        parsed = parse_arguments(arguments)
        source_path = resolve_source_path(parsed.plant)
        document = load_source_document(source_path)
        output_path = parsed.output or source_path.with_suffix(".html")
        if parsed.historical_xml:
            historical = load_historical_plant(parsed.historical_xml)
            if historical.name != document.name:
                raise ValueError(
                    "Historical XML controlpoint name must match the source document name."
                )
            output_path.write_text(
                build_tabbed_reconciliation_packet(
                    document, historical, parsed.historical_pdf
                ),
                encoding="utf-8",
            )
            print(f"Generated {output_path}")
            return 0
        errors = validate_diagram(document)
        if errors:
            for error in errors:
                print(f"INCOMPLETE: {error}", file=sys.stderr)
            output_path.write_text(
                build_incomplete_packet(document, errors), encoding="utf-8"
            )
            return 1

        output_path.write_text(build_packet(document), encoding="utf-8")
        print(f"Generated {output_path}")
        return 0
    except ValueError as error:
        print(f"INCOMPLETE: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
