# Signal symbols under the supply/demand shape (worklist, 2026-11-03)

Working direction, not ratified. Trackplan mast = demand (`Indications`, rulebook words); field device = supply
(Style = manufacturer model, pins = how the layout wires it); the derivation matches the two. Heads are not drawn:
a head alone states no fact (Glossary: aspect). `*` marks a default the owner has not ruled on.

## Trackplan (Railroad-Trackplan)

| symbol | Role | Appliance | Style | Kind | fields | pins | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Signal Mast Single CONTROLLED | APPLIANCE | mast | single | CONTROLLED | Name=${Value}, Indications= | SIGNAL | Interlocking signal, one head drawn. Indications: the rulebook names this mast must show, comma-separated. |
| Signal Mast Single ABSOLUTE | APPLIANCE | mast | single | ABSOLUTE | same | SIGNAL | Block signal, Stop and Hold, one head drawn. |
| Signal Mast Single PERMISSIVE | APPLIANCE | mast | single | PERMISSIVE | same | SIGNAL | Block signal with number plate, one head drawn. |
| Signal Mast Double CONTROLLED | APPLIANCE | mast | double | CONTROLLED | same | SIGNAL | Two heads drawn; the head count is picture, the devices decide. |
| Signal Mast Triple CONTROLLED * | APPLIANCE | mast | triple | CONTROLLED | same | SIGNAL | Three heads drawn. |
| Signal Mast Dwarf CONTROLLED | APPLIANCE | mast | dwarf | CONTROLLED | same | SIGNAL | Dwarf; Style dwarf is a model fact. |
| Stop Sign * | APPLIANCE | mast | stop_sign | ABSOLUTE * | Name=${Value}, Indications=Stop (fixed) | SIGNAL | A fixed Stop: painted post or one red lamp. The only form with a fixed demand. |
| Signal Mast Plate-R, Plate-G | POLICY | | | RULE_29x | unchanged | To | unchanged |
| Train Order Mast | APPLIANCE | train_order | | | Name=${Value}, Station= | H today, none later * | Demand fixed by reference data (Stop, Receive Orders, Proceed); N/S heads become devices. Later step. |
| Signal Head - CL / CPL / Semaphore-LQ / Semaphore-UQ | | | | | | | retired |

## Field (Railroad-Field)

| symbol | Role | Appliance | Style | fields | pins (Pin.X=kind) | Description |
| --- | --- | --- | --- | --- | --- | --- |
| Device-Head-TypeD | DEVICE | head | TypeD | Name=${Value} | IND=indication, R=binary, Y=binary, G=binary | GRS Type D, three lamps, one wire each. Name = mast + head letter (784A). Was Device-Head-CPL. |
| Device-Head-TypeD-Encoded | DEVICE | head | TypeD | Name=${Value} | IND=indication, S0=binary, S1=binary | Type D behind a two-bit decoder on the head. Was -CPL-Encoded. |
| Device-Head-TypeD-Pixel | DEVICE | head | TypeD | Name=${Value}, Address= | IND=indication, RGB=color | Type D as three points on a pixel bus. Was -CPL-Pixel. |
| Device-Head-SA-RGB | DEVICE | head | SA | Name=${Value} | IND=indication, R=binary, G=binary, B=binary | GRS SA searchlight as one RGB LED, three legs. Was -CL-RGB. |
| Device-Head-SA-Pixel | DEVICE | head | SA | Name=${Value}, Address= | IND=indication, RGB=color | SA searchlight as one pixel. Was -CL-Pixel. |
| Device-Head-H2-RGB, -H2-Pixel * | DEVICE | head | H2 | as SA | as SA | US&S H-2 searchlight; same reference row as SA today. |
| Device-Head-Semaphore-UQ | DEVICE | head | UQ | Name=${Value}, stop_deg, approach_deg, clear_deg | IND=indication, ARM=position | unchanged; three positions, no flash. |
| Device-Head-Semaphore-LQ | DEVICE | head | LQ | same | same | unchanged; two positions, no flash. |
| Mast (JMRI whole-mast) | DEVICE | mast | | Name=${Value} | IND=indication (output) | unchanged. |

Changes beyond names: the `Head` field goes (the letter is the Name's last letter; identity never from a binding);
device Style is the model, never the mechanism (the pins say the wiring), so one supply row covers TypeD, -Encoded
and -Pixel.

Reference rows to seed as encountered: TypeD = red, yellow, green, flashes, one head. SA, H2 = same. UQ = three
positions, no flash. LQ = two positions, no flash. Type G, P-5, N-2 wait for a drawing.

Model side after the symbols exist: `Indications` on the mast (given), device model table (reference), heads derived
from devices by Name, the match derivation with its diagnostics (no devices = missing; a device that cannot show a
demanded indication = error), schema additive change; one ADR line moving "head casts with Head letter" to the field
sheet.
