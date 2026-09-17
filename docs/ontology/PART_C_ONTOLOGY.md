# Part C Ontology and Contract Boundaries

## Purpose

This document defines the concepts and invariants required before the project creates topology, train progression, or documentation-generator implementations. It makes the reconstructed SPCoast dispatcher territory reviewable without confusing visual appearance, operations paperwork, historical implementation details, and vital railroad behavior.

## Authority boundaries

The project uses five separate authoritative domains.

1. **Interlocking Plant source document** defines the complete plant design. Studio or compatible design tooling preserves it and compiles its vital information into a deployable Vital Payload.
2. **Runtime vital model** is the in-memory FieldUnit Interlocking Plant created from a Vital Payload. It owns appliances, routes, and safety logic during execution.
3. **Operating topology** defines permitted modeled movement between detection points and the circuit occupancy that movement applies.
4. **Track diagram representation** defines the schematic presentation, annotation, and cross-artifact references. It does not create topology.
5. **Operations** defines the business purpose of movements: locations, freight intent, train service, paperwork, and crew work. It consumes accepted topology and does not create it.

The cTc Machine is supervisory. Its lever positions are intent, not field truth. The physical desk is a lifecycle constraint on CodeLine allocation after construction, not an alternate plant model. The active scope is a dispatcher territory, not the complete geographic subdivision or every railroad operation beyond its boundaries.

## Guiding axioms

1. An `InterlockingPlant` is the only owner of vital route, signal, locking, and indication behavior. The simulation overlay can update its track-circuit occupancy only through supported FieldUnit interfaces.
2. An `InterlockingPlant`, `ControlledPoint`, and `PanelColumn` are distinct entities. No alias or display convenience can erase those boundaries.
3. A `ModelDetectionBlock` always represents detectable modeled occupancy and binds explicitly to one or more named plant `TrackCircuit` entities.
4. A `TransitSegment` connects modeled detection points. It may compress distance but cannot imply detection that has not been modeled.
5. A `PrototypeRedaction` records omitted or dramatically compressed prototype geography. It cannot bind occupancy, authorize traversal, or become a topology edge.
6. A dark or simplified drawing is only a rendering decision. If it denotes an operating function, its topology and safety-relevant behavior remain explicit outside the drawing.
7. A diagram reference, geographic image, station ordering, shared circuit name, train schedule, waybill, switch list, or historical implementation artifact never proves a plant or topology relationship by itself.
8. Every reviewable claim has a stable identity, evidence record, and disposition. An incomplete or provisional claim cannot support automated movement.
9. A physical desk allocation is a lifecycle interlock. A compatible profile validates against it; neither artifact silently changes to fit the other.
10. An Interlocking Plant Source Document can be incomplete while it is authored. Commands state the completeness they require and report missing optional members explicitly.
11. The source document → Vital Payload transformation is lossy and one-way. A Vital Payload may create Runtime Interlocking Plant state, but can never rebuild, update, or overwrite an Interlocking Plant Source Document.

## Relationship taxonomy

### Vital and supervisory

```text
InterlockingPlant
  owns -> TrackCircuit, Appliance, SignalRoute
ControlledPoint
  addresses -> InterlockingPlant [one or more]
PanelColumn
  represents -> ControlledPoint
DeskAllocation
  allocates -> PanelColumn, CodeLine token
```

### Operating topology

```text
TopologyNode
  is -> PlantBoundary | DetectionEndpoint | Junction | Terminal
ModelDetectionBlock
  binds -> TrackCircuit [one or more]
  connects -> TopologyNode [two or more]
TransitSegment
  connects -> TopologyNode [exactly two]
  progresses_to -> ModelDetectionBlock | TransitSegment
PrototypeRedaction
  contextualizes -> diagram area | named prototype area
```

A topology route is an ordered traversal of accepted detection blocks and transit segments. It is not a FieldUnit `SignalRoute`, although a traversal may cause a bound circuit to be occupied and therefore invoke plant safety logic.

### Diagram representation

```text
TrackDiagramDocument
  contains -> DiagramSheet
DiagramSheet
  contains -> DiagramNode, DiagramJunction, DiagramSegment, Overlay
Diagram element
  references -> Plant entity | Topology entity | Evidence assertion
```

Diagram geometry is descriptive. A `DiagramSegment` must not be promoted into an operating `TransitSegment` merely because it joins two symbols on a page.

### Operations

```text
OpsLocation
  contains -> OpsTrack
Industry
  is a role of -> OpsLocation or OpsTrack
TrainRoute
  visits -> OpsLocation [ordered]
Train
  operates_on -> TrainRoute
CarWorkIntent
  directs -> RollingStock to OpsLocation or OpsTrack
CrewAssignment
  assigns -> CrewMember to Train and/or Job
```

`SignalRoute` and `TrainRoute` are intentionally distinct terms.

## Evidence and review model

Each assertion records:

- a stable assertion identifier;
- a subject and predicate reference;
- an optional object reference or literal;
- one or more evidence citations;
- one of `accepted`, `provisional`, `rejected`, or `incomplete`;
- reviewer and decision timestamp when reviewed.

`accepted` means the assertion is eligible for the model behaviors explicitly covered by its evidence. It does not claim that the project has recreated all prototype physical detail. `provisional`, `rejected`, and `incomplete` assertions must render visibly as such in review artifacts.

## Interlocking Plant source document

`CP_*.json` is the complete Interlocking Plant Source Document. The current root-level fields—such as `name`, `trackCircuits`, `switches`, `signalMasts`, and `routes`—provide the vital information that a compiler projects into a Vital Payload.

The source document adds optional namespaces:

- `design` contains the Track Diagram Document, evidence ledger, review status, and non-vital design annotations;
- `supervision` contains Controlled Point, CodeLine, and physical Panel Column allocation information.
- `physical` contains optional field-node, I/O, and constructed-hardware realization information.

The source document is saved by source-aware tooling. Studio or a compatible compiler derives a Vital Payload from the vital members. FieldUnit reads the Vital Payload to create Runtime Interlocking Plant state. It does not read/write the source document as part of its runtime lifecycle.

The current direct loading of `CP_*.json` into FieldUnit remains a transitional compatibility path while the compiler is introduced. The current `PlantSerializer::serialize()` output is a legacy vital-only export, not a complete source-document rewrite or the future compiler authority. No live mutation/update interface is needed for this decision. If runtime reconfiguration is later needed, it requires its own safe lifecycle and atomic validation design.

## Historical source policy

ArduinoPoint XML, generated sketches, wiki pages, and archived photographs are informational evidence. They establish historical context, identify larger layout relationships, and expose omitted or contradictory details for review. They do not override FieldUnit’s AAR/relay-logic implementation and do not import obsolete startup, CodeLine, display, or transport procedures into the new system.

Historical material is cited in the evidence ledger with its date and artifact type. A source-document assertion becomes usable only after it has an explicit disposition and supporting evidence appropriate to the claim.

## Track Diagram Document

The Track Diagram Document is the tool-neutral, versioned diagram member of the Interlocking Plant Source Document. It is initially created and validated in this repository. FieldUnit-Studio can later implement compatible import, editing, and export after this contract has proven useful.

The minimum diagram vocabulary is:

- documents and sheets;
- nodes: anchors, terminals, and sheet seams;
- typed ports;
- junctions: turnout, crossover, slip, diamond, turntable, and traverser;
- segments between typed ports;
- visual styles and geometry;
- `EntityRef` bindings to plant/topology identities;
- overlays, labels, decorations, and display levels;
- evidence/status annotations.

The diagram contract deliberately excludes FieldUnit routes, CodeLine encoding, JMRI manager tables, occupancy state, schedules, waybills, and crew tasks.

## Validation gates

### Validated plant profile

A profile is validated for automated use only when it:

1. conforms to the ontology and applicable schemas;
2. deserializes and round-trips through FieldUnit;
3. has a source-document `design.diagram` member that references every visualizable declared entity;
4. renders all routes, circuit/appliance data, and CodeLine ledger entries in its single-plant packet;
5. has a reviewed evidence/disposition for all safety-relevant reconstructed claims;
6. validates against the constructed desk allocation when that allocation exists.

### Proven operating topology

A connection is eligible for automatic progression only when:

1. its endpoint nodes, detection blocks, and transit segments have stable identities and reviewed evidence;
2. each detection block binds the plant circuits that it will shunt;
3. compressed travel is represented by an explicit transit segment, not an invented detection block;
4. prototype redactions remain context-only metadata;
5. deterministic trace tests prove occupancy, knockdown, locking, and release in every supported direction.

## Reference-model lessons

JMRI Layout Editor provides useful prior art for typed ports, track segments, edge connectors, and diagram-to-block references. Its `layout-config` persistence couples panels to global JMRI configuration and is not this project’s interchange format.

JMRI OperationsPro, CATS, and TrainCrew demonstrate that work locations, manifests, crew assignment, and timed crew tasks are valuable operational concerns. They are intentionally deferred from topology and vital plant definitions.

ArduinoPoint harvesting is useful primarily for the broader dispatcher-territory context and for gap-filling. Its legacy sketches are not a replacement for FieldUnit vital logic.

See `docs/research/PART_C_REFERENCE_MODELS.md` for citations and scope limits.
