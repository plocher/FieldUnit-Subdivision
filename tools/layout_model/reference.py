"""Reference data: general facts, not layout data (ADR 0008 §4.7, ADR 0012 §6). A placeholder: the tables a writer and
the reference derivation share, each versioned so provenance can name it. Contents are TBD by the owner; only the
lookup is fixed.
"""
from __future__ import annotations

# Versioned so provenance can name it.
REFERENCE_DATA = {"encodingTransportPairing": "2026-10-23", "driverEncodings": "2026-10-23"}
# An encoding's Kind pairs with its transport's Kind (ADR 0009 §3.10).
TRANSPORT_OF_ENCODING = {"AAR": "MQTT", "USS506": "TIMECODE", "BITS": "TIMECODE", "JMRI": "MQTT", "CMRI": "CMRI"}
# A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009 §3.3, §3.6, §3.12 "IC native or encoded").
ENCODING_OF_IC = {"MQTT-JMRI": "JMRI"}
