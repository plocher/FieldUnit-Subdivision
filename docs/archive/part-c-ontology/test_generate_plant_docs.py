"""Tests for the single-plant documentation packet command."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPOSITORY_ROOT / "tools" / "generate_plant_docs.py"


class GeneratePlantDocsCliTests(unittest.TestCase):
    """Verify the supported single-plant documentation command."""

    def test_positional_source_path_generates_offline_packet_from_embedded_diagram(
        self,
    ) -> None:
        """A source document produces a packet at its default output path."""
        source_document = {
            "$schema": "https://fieldunit.org/schema/v1/interlocking-plant.schema.json",
            "version": "1.0.0",
            "name": "CP_Test",
            "trackCircuits": [{"name": "1T1", "dropoutDelayMs": 0}],
            "switches": [{"name": "1"}],
            "signalControls": [{"name": "2"}],
            "signalMasts": [{"name": "2SA", "type": "TWO_HEAD"}],
            "detectorLocks": [{"switch": "1", "trackCircuit": "1T1"}],
            "routes": [
                {
                    "name": "MAIN-ROUTE",
                    "governedBy": {"signal": "2", "direction": "RIGHT"},
                    "displays": {
                        "mast": "2SA",
                        "head": 0,
                        "maxIndication": "CLEAR",
                    },
                    "aligns": [{"switch": "1", "position": "NORMAL"}],
                    "clears": ["1T1"],
                    "entrance": "1T1",
                }
            ],
            "design": {
                "status": "review",
                "diagram": {
                    "kind": "track-diagram",
                    "version": "1.0.0",
                    "id": "CP_Test.diagram",
                    "subject": {"kind": "interlockingPlant", "id": "CP_Test"},
                    "sheets": [
                        {
                            "id": "main",
                            "name": "Main Diagram",
                            "nodes": [
                                {
                                    "id": "west",
                                    "kind": "terminal",
                                    "position": {"x": 10, "y": 60},
                                    "ports": [{"id": "east"}],
                                },
                                {
                                    "id": "east",
                                    "kind": "terminal",
                                    "position": {"x": 290, "y": 60},
                                    "ports": [{"id": "west"}],
                                },
                            ],
                            "junctions": [],
                            "segments": [
                                {
                                    "id": "main-line",
                                    "from": {"elementId": "west", "portId": "east"},
                                    "to": {"elementId": "east", "portId": "west"},
                                    "geometry": {"kind": "straight"},
                                    "style": {
                                        "trackClass": "mainline",
                                        "stroke": "solid",
                                        "visibility": "visible",
                                    },
                                    "refs": [
                                        {"kind": "trackCircuit", "id": "1T1"}
                                    ],
                                }
                            ],
                            "overlays": [
                                {
                                    "id": "label-1T1",
                                    "kind": "label",
                                    "position": {"x": 150, "y": 48},
                                    "text": "1T1",
                                    "refs": [
                                        {"kind": "trackCircuit", "id": "1T1"}
                                    ],
                                }
                            ],
                        }
                    ],
                },
                "evidence": {
                    "kind": "evidence-ledger",
                    "version": "1.0.0",
                    "id": "CP_Test.evidence",
                    "sources": [],
                    "assertions": [],
                },
            },
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "CP_Test.json"
            source_path.write_text(json.dumps(source_document), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(GENERATOR_PATH), str(source_path.with_suffix(""))],
                check=False,
                capture_output=True,
                text=True,
            )

            output_path = source_path.with_suffix(".html")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())

            packet = output_path.read_text(encoding="utf-8")
            self.assertIn("CP_Test — Plant Documentation", packet)
            self.assertIn('<svg class="track-diagram"', packet)
            self.assertIn('data-diagram-id="main-line"', packet)
            self.assertIn("MAIN-ROUTE", packet)
            self.assertIn("1T1", packet)
            self.assertIn(
                "<th>Route</th><th>Signal mast</th><th>Switch alignment</th>"
                "<th>Required clear blocks</th><th>Indication</th>",
                packet,
            )
            self.assertIn("<td>1</td>", packet)
            self.assertNotIn(">RIGHT<", packet)
            self.assertNotIn("NORMAL", packet)
            self.assertNotIn('src="http', packet)
    def test_missing_diagram_generates_incomplete_review_report(self) -> None:
        """A draft source document reports its missing diagram without inference."""
        source_document = {
            "$schema": "https://fieldunit.org/schema/v1/interlocking-plant.schema.json",
            "version": "1.0.0",
            "name": "CP_Draft",
            "design": {"status": "incomplete"},
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "CP_Draft.json"
            source_path.write_text(json.dumps(source_document), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(GENERATOR_PATH), str(source_path)],
                check=False,
                capture_output=True,
                text=True,
            )

            output_path = source_path.with_suffix(".html")
            self.assertEqual(result.returncode, 1)
            self.assertTrue(output_path.exists())
            packet = output_path.read_text(encoding="utf-8")
            self.assertIn("CP_Draft — Incomplete Plant Documentation", packet)
            self.assertIn("design.diagram", packet)
            self.assertIn("must be a JSON object.", packet)
    def test_historical_xml_generates_reconciliation_packet(self) -> None:
        """A historical XML source produces a comparison packet for a draft plant."""
        source_document = {
            "$schema": "https://fieldunit.org/schema/v1/interlocking-plant.schema.json",
            "version": "1.0.0",
            "name": "CP_Test",
            "trackCircuits": [{"name": "1T1", "dropoutDelayMs": 0}],
            "switches": [{"name": "1"}],
            "detectorLocks": [{"switch": "1", "trackCircuit": "1T1"}],
            "supervision": {
                "panelColumns": [
                    {
                        "number": 1,
                        "switchId": "1",
                        "switchName": "783",
                        "signalId": "2",
                        "signalName": "784",
                    },
                    {
                        "number": 2,
                        "lockId": "3",
                        "lockName": "795",
                        "lockedPosition": "NORMAL",
                        "unlockedControl": "local",
                    },
                ]
            },
            "design": {
                "status": "incomplete",
                "historicalPresentation": {
                    "officeSketch": {
                        "station": "CP_Test",
                        "columns": [
                            {
                                "number": 1,
                                "switch": "1",
                                "trackLamps": ["1T1"],
                            }
                        ],
                    },
                    "routeTable": [
                        {
                            "mast": "2SAB",
                            "alignment": "1",
                            "heads": [
                                {
                                    "name": "A",
                                    "requirements": ["1T1", "SIG2(RIGHT)"],
                                    "indication": "CLEAR",
                                }
                            ],
                        }
                    ],
                },
                "review": {
                    "routeFindings": [
                        {
                            "route": "SB-INDUSTRY-DIV",
                            "disposition": "rejected",
                            "reason": "Switch 3 is trailing for the southbound move.",
                        }
                    ]
                },
            },
        }
        historical_xml = """\
<controlpoint name="CP_Test" layout="Example" node="0x01">
  <doc>Recovered comparison source.</doc>
  <switches>
    <switch name="1" trackcircuit="1T1" />
    <switch name="3" trackcircuit="3T1" />
  </switches>
  <trackcircuits>
    <trackcircuit name="1T1" />
    <trackcircuit name="3T1" />
  </trackcircuits>
  <signals>
    <signal name="2"><head name="H2SA" direction="S">
      <route name="MAIN"><switch name="1" position="N" /></route>
    </head></signal>
  </signals>
  <controls><control name="1NW" word="0" bit="0" /></controls>
  <indications><indication name="1NW" word="0" bit="0" /></indications>
</controlpoint>
"""

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_path = temporary_path / "CP_Test.json"
            historical_path = temporary_path / "CP_Test.xml"
            historical_pdf_path = temporary_path / "CP_Test.pdf"
            output_path = temporary_path / "CP_Test-reconciliation.html"
            source_path.write_text(json.dumps(source_document), encoding="utf-8")
            historical_path.write_text(historical_xml, encoding="utf-8")
            historical_pdf_path.write_bytes(b"%PDF-1.4\n% test evidence\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR_PATH),
                    str(source_path),
                    "--historical-xml",
                    str(historical_path),
                    "--historical-pdf",
                    str(historical_pdf_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            packet = output_path.read_text(encoding="utf-8")
            self.assertIn("CP_Test — Reconciliation Packet", packet)
            self.assertIn("Recovered comparison source.", packet)
            self.assertIn('<pre class="historical-note">', packet)
            self.assertIn("Current source document", packet)
            self.assertIn("Historical XML source", packet)
            self.assertIn('data-tab="historical"', packet)
            self.assertIn('data-tab="current"', packet)
            self.assertIn('data-tab="combined"', packet)
            self.assertIn('id="historical"', packet)
            self.assertIn('id="current"', packet)
            self.assertIn('id="combined"', packet)
            self.assertIn("data:application/pdf;base64,", packet)
            self.assertIn("Current named routes", packet)
            self.assertNotIn("Current named vital routes", packet)
            self.assertIn("783", packet)
            self.assertIn("784", packet)
            self.assertIn("795", packet)
            self.assertIn("Locked = NORMAL", packet)
            self.assertIn("Unlocked = local control", packet)
            self.assertIn("3T1", packet)
            self.assertIn("Historical only", packet)
            self.assertIn("machine.addStation(&quot;CP_Test&quot;)", packet)
            self.assertIn("2SAB", packet)
            self.assertIn("SIG2(RIGHT)", packet)
            self.assertIn("Detector locks", packet)
            self.assertIn("3 / 3T1", packet)
            self.assertIn("Route review findings", packet)
            self.assertIn("Switch 3 is trailing for the southbound move.", packet)
            self.assertIn("No track diagram was inferred", packet)


if __name__ == "__main__":
    unittest.main()
