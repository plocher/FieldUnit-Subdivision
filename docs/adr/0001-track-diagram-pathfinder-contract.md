# ADR 0001: Define a tool-neutral Track Diagram Document before Studio integration

## Status

Accepted for Part C.A.

## Context

FieldUnit-Subdivision needs visual plant packets and an overhead model board. FieldUnit-Studio has relevant graph, component, and canvas work, but it is immature and is resolving the same domain boundaries. Making Studio's current persistence model the source of truth would freeze unproven assumptions into the Part C runtime.

JMRI PanelPro is useful prior art but persists a coupled layout configuration, not a portable diagram-only contract.

## Decision

Part C defines and validates a versioned, tool-neutral Track Diagram Document in FieldUnit-Subdivision. It is a member of the complete Interlocking Plant source document. Studio or a compatible compiler creates a lossy Vital Payload for FieldUnit runtime use. The source document has stable references to plant and topology entities but does not contain vital logic, operational paperwork, or inferred topology.

Issue #1 consumes this contract for single-plant documentation first. FieldUnit-Studio is a future compatible importer/editor/exporter after the contract, test fixtures, and validation behavior have been proven.

## Consequences

- The current work can validate reconstructed plants without waiting for Studio maturity.
- The contract becomes a concrete pathfinder for Studio rather than a second uncoordinated visual model.
- Studio integration requires compatibility tests and may require adaptation of its current graph/coordinate persistence.
- No tool may silently derive plant or topology facts from diagram geometry or historical implementation artifacts.
- FieldUnit vital serialization is not a source-document write path; the Vital Payload cannot rebuild the source document.
