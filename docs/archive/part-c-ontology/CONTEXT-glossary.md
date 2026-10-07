# FieldUnit-Subdivision Domain Glossary

## Safety and supervision

**Interlocking Plant**
: A local vital field-safety entity. It owns appliances, routes, route locking, signal behavior, and track-circuit interpretation.

**Controlled Point / Line Station**
: An addressable unit on a supervisory CodeLine. Its available controls and indications are constrained by the selected coding system.

**Panel Column**
: A fixed physical slice of a dispatcher console. It is a representation of a Controlled Point allocation, not a field-safety entity.

**cTc Machine**
: The supervisory office console. Its controls express intent. Its indications show verified field state.

**Dispatcher Territory**
: The bounded area supervised by one cTc Machine. It may be only part of a named railroad subdivision.

**Signal**
: A named functional set of masts that protects an Interlocking Plant junction. The Signal is not one mast and is not one of its heads.

**Signal Mast**
: A directional physical mast controlled by a Signal. A southbound mast protects southbound traffic; a northbound mast protects northbound traffic.

**Signal Head**
: One display unit on a Signal Mast. Head letters distinguish multiple heads on the same directional mast. Historical shorthand such as `2SAB` denotes Signal 2's southbound mast with heads A and B; it is not the Signal's canonical identity.

**Switch**
: A named first-class appliance that aligns a track path. Its canonical Name is used in all functional references. Historical relay ordinals such as `1`, `3`, and `5` are informational evidence only when the canonical Switch names are `783`, `795`, and `799`.

## Operating representation

**Track Circuit**
: A field detection input owned by an Interlocking Plant. A simulation overlay may apply its occupancy but does not decide its vital consequences.
**Track Net**
: A named KiCad wire/net that represents one logical track path. Its net label is the authoritative name for that path.

**Insulated Rail Joint (IRJ)**
: An inline boundary between track nets. An IRJ can exist for Track Circuit, APB, ABS, or other railroad purposes; it does not by itself identify a controlled-point boundary. A Signal IRJ adds a Signal Mast attachment pin.

**Switch OS Track Circuit**
: The standard occupancy region associated with a Switch. Its name is derived as `<SwitchName>T1`, such as `783T1`, and spans the Switch C, N, and R path nets even though KiCad keeps those paths separate.

**Track Designation**
: A rulebook or operational label such as `MT`, `MT1`, or `MT2`. It is distinct from a Track Net or Track Circuit name and can vary by operating policy.

**Model Detection Block**
: A named portion of the model with detectable occupancy. It explicitly binds to one or more Track Circuits and has defined traversal directions.

**Transit Segment**
: A modeled connection between detection points. It represents movement across a distance without claiming additional detection.

**Prototype Redaction**
: A documented omission or severe geographic compression of prototype material. It provides context only. It is not track, a route, a Transit Segment, or a Model Detection Block.

**Track Diagram Document**
: A versioned, tool-neutral schematic artifact. It represents and annotates track visually through stable references to authoritative plant and topology entities.
**Interlocking Plant Source Document**
: The complete, versioned `plant.json` design source. It is preserved by Studio/design tooling and compiled into a Vital Payload. Its optional `design` and `supervision` members provide non-vital design context and implementation constraints.

## Evidence and lifecycle

**Evidence**
: A cited source or a documented modeling decision that supports a claim. Examples include prototype documents, physical desk observations, and operator knowledge.

**Disposition**
: The review state of a claim: `accepted`, `provisional`, `rejected`, or `incomplete`.

**Lifecycle Interlock**
: A constructed physical desk allocation that constrains compatible CodeLine definitions. Validation must report mismatches; it must never rewrite either design silently.
**Vital Projection**
: The lossily compiled subset of an Interlocking Plant Source Document that FieldUnit requires at runtime.

**Vital Payload**
: A deployable serialized Vital Projection emitted by Studio or a compatible compiler. FieldUnit reads it to construct runtime vital state. It cannot recreate or update an Interlocking Plant Source Document.

**Runtime Interlocking Plant**
: The FieldUnit in-memory execution object created from a Vital Payload. It applies vital logic but does not own source-document design data.

**Physical Field Realization**
: Optional source-document information about field node, I/O, and constructed hardware. It constrains implementation but does not change vital logic.

**Historical Implementation Evidence**
: Informational material from a prior implementation, such as ArduinoPoint sketches. It can provide context, fill gaps, or reveal conflicts, but does not override FieldUnit vital logic or become authoritative by itself.

## Operations

**Signal Route**
: An Interlocking Plant route governed by signals and vital safety rules.

**Train Route**
: An ordered sequence of operational locations served by a train. It is not a Signal Route.

**Ops Location**
: A place where a train has work, such as an industry, yard, interchange, staging location, or division point.

**Ops Track**
: A named capacity/work location within an Ops Location. Its kind can be spur, yard, interchange, or staging.

**Car Work Intent**
: A description of car movement purpose, such as current load, final destination, and return condition. It is a future operations concern, not plant or topology truth.
