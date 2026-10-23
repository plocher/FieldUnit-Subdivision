# Glossary delta proposed to FieldUnit, 2026-10-23

For `~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md`, the vocabulary source of truth. The naming
audit of 2026-10-22 (`naming-audit-2026-10-22.md` §2) found the seam vocabulary of ADR 0009 undefined there.
These are the definitions ADR 0009 gives them; the owner edits the glossary.

| Term | Proposed definition |
|---|---|
| processor | The thing logic runs on and connections are anchored on: a field processor, the CTC machine's processor, or a virtual host application. A unit runs on exactly one. |
| transport | A mechanism that carries encodings: an MQTT broker, a CMRInet serial line, a US&S time-code line, LocoNet. Declared once; placed once per processor that connects to it. Bindable to either seam. |
| encoding | What rides a transport. A code line encoding (AAR tokens, US&S 506, bit packing) provides a code line; an I/O encoding (JMRI over MQTT, CMRInet polling) provides remote I/O for the processor that anchors its transport instance. |
| code line | A code line encoding on a transport, as a thing units and the machine attach to. One per unit. |
| IOBus, bus | A processor's device interface, or a CMRInet node's: what drivers attach to with their address. |
| driver | A chip or object with an address on a bus, declaring device pins: an I2C expander, a GPIO pin or pixel chain, a JMRI object, a CMRInet node or one of its bits. |
| node (CMRInet) | A driver on a CMRInet line, addressed by its UA, declaring its input and output byte arrays and providing a bus for its bits. Not a processor. Narrowed from the retired general sense. |
| host | Retired. Where it meant "runs on", say processor; where it meant the CMRInet master, say the processor that anchors the transport. |
| port | A unit sheet's connection to the layout: Codeline, Processor, IOBus, PanelIOBus. |
| seam | After FieldUnit ADR 0005: Seam 1, the code line between office and field logic; Seam 2, hardware I/O, local or remote, on the panel side and the field side. |
| local I/O, remote I/O | Drivers on a processor's own bus; drivers reached through an encoding on a transport (JMRI) or through a node on a line (CMRInet). |
| head device | The hardware that renders a head's aspects: aspect to I/O, with the style fixed per symbol. The trackplan head owns indication to aspect. Prose says head device, not cast. |
| house | Instrument house: the structure at a control point that holds its field equipment; `House` symbol. Bungalow is the prototype's word for a walk-in house; case for a cabinet. |
| field station | Unchanged, now derived: one per interlocking on an AAR line, one per house on a 506 line. |
| OfficeUnit, FieldUnit | The owner's rulings of 2026-10-23: say OfficeUnit, not machine; FieldUnit, not unit; CMRInet Node and CMRInet Host, not node and host; Driver, not chip; an OfficeUnit's columns, not its lines; KiCad symbol units, never units. |
