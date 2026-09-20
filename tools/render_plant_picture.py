#!/usr/bin/env python3
"""Render a compiled plant topology as DOT or Graphviz SVG."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from kicad_services.netlist_reader import NetlistParseError  # noqa: E402
from kicad_services.symbol_library_reader import SymbolLibraryParseError  # noqa: E402
from parse_kicad_plant import load_graph  # noqa: E402
from plant_graph.picture import (  # noqa: E402
    render_dot,
    render_layout_overview_svg,
    render_model_board_svg,
    render_route_board_svg,
    render_swim_lane_svg,
)


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the static picture-probe command-line parser."""
    parser = argparse.ArgumentParser(
        description="Render KiCad-derived topology, route, or source-board review views."
    )
    parser.add_argument("--library", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--schematic", type=Path)
    source.add_argument("--netlist", type=Path)
    parser.add_argument("--kicad-cli", type=Path, default=None)
    parser.add_argument("--aliases", type=Path, default=None)
    parser.add_argument("--route", help="Optional structural route name to highlight")
    parser.add_argument(
        "--format",
        choices=(
            "dot",
            "svg",
            "swim-svg",
            "board-svg",
            "route-board-svg",
            "overview-svg",
        ),
        default="dot",
    )
    parser.add_argument("--dot", type=Path, default=Path("dot"))
    parser.add_argument("--output", type=Path, default=None)
    return parser


def render_svg(dot_source: str, executable: Path) -> str:
    """Render DOT source through Graphviz and return SVG text."""
    result = subprocess.run(
        (str(executable), "-Tsvg"),
        input=dot_source,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Graphviz dot failed")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    """Run the static topology picture probe."""
    args = build_arg_parser().parse_args(argv)
    try:
        graph = load_graph(args)
        if args.format == "overview-svg":
            content = render_layout_overview_svg(graph)
        elif args.format == "board-svg":
            if args.route is not None:
                raise ValueError("--route requires --format route-board-svg")
            content = render_model_board_svg(graph)
        elif args.format == "route-board-svg":
            content = render_route_board_svg(graph, route_name=args.route)
        elif args.format == "swim-svg":
            if args.route is None:
                raise ValueError("--route is required for --format swim-svg")
            content = render_swim_lane_svg(graph, route_name=args.route)
        else:
            dot_source = render_dot(graph, route_name=args.route)
            content = (
                dot_source
                if args.format == "dot"
                else render_svg(dot_source, args.dot)
            )
    except (
        FileNotFoundError,
        NetlistParseError,
        SymbolLibraryParseError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output is None:
        sys.stdout.write(content)
    else:
        args.output.write_text(content, encoding="utf-8")
    return 1 if graph.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
