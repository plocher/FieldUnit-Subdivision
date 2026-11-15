Feature: A binding states the facts of the wire it is drawn as
  A device pin wired to a driver pin is a binding. Its route names the bus owner, the address and the driver pin.
  It also states the driver pin's number, as the driver symbol has it. What the number means on the chip is the driver's knowledge.
  Its direction comes from the device pin's electrical type. At the device-to-driver boundary the types are opposite by design: the logic drives a pin the device takes in (output) and reads a pin the device puts out (input). A driver has no direction of its own.
  A passive pin is a junction, not a boundary: it states no direction, and that is not a finding. Any other pin type with no direction is reported as missing.
  A boolean pin (its library kind is binary) states its sense, the asserted level: low for a pin drawn ~{X}, high for a plain name, and the other one when the device's Invert names the pin. A pin of another kind has no sense, and an Invert that names one is an error.
  A JMRI mast device on a processor's bus stands in for a remote JMRI mast. It is a whole-mast consumer of the mast it names, and the logic drives it. Its Address is JMRI's identifier, kept as stated, never its key.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                 | Role     | Appliance | IC      | Address | Name   | Invert | Pin.M  | Pin.OCC | Pin.LAMP | Pin.A      | Pin.VALUE |
      | X1  | Railroad-HardwareIO:Driver-I2C-MAX7313 | IODRIVER |           | MAX7313 | 0x20    |        |        |        |         |          |            |           |
      | DS  | Railroad-Field:Device-Switch-OS        | DEVICE   | switch    |         |         | 3      |        | binary | binary  |          |            |           |
      | DL  | Railroad-Field:Device-Lamp             | DEVICE   | lamp      |         |         | 1L     | LAMP   |        |         | binary   |            |           |
      | DM  | Railroad-Field:Device-Mast-Dwarf       | DEVICE   | mast      |         |         | 2NA    |        |        |         |          | indication |           |

  Scenario: a switch machine and its occupancy
    Given these nets:
      | Net | Pins                      |
      | bus | P1.IOBus X1.IOBus         |
      | m   | DS.M[input] X1.A1#1       |
      | occ | DS.~{OCC}[output] X1.B1#9 |
    When the drawing is imported
    Then the device "DS" binds "M" to "Alpha/0x20/A1" on driver pin 1, output, asserted high
    And the device "DS" binds "OCC" to "Alpha/0x20/B1" on driver pin 9, input, asserted low

  Scenario: a lamp whose Invert names its pin
    Given these nets:
      | Net | Pins                      |
      | bus | P1.IOBus X1.IOBus         |
      | l   | DL.~{LAMP}[input] X1.A2#2 |
    When the drawing is imported
    Then the device "DL" binds "LAMP" to "Alpha/0x20/A2" on driver pin 2, output, asserted high

  @binding.direction
  Scenario: a mast's passive position pin bound to a driver
    Given these nets:
      | Net | Pins                  |
      | bus | P1.IOBus X1.IOBus     |
      | a   | DM.A[passive] X1.A3#3 |
    When the drawing is imported
    Then the device "DM" binds "A" to "Alpha/0x20/A3" on driver pin 3, no direction, with no sense
    And it is not reported

  @binding.direction
  Scenario: a device pin typed unspecified bound to a driver
    Given these nets:
      | Net | Pins                      |
      | bus | P1.IOBus X1.IOBus         |
      | m   | DS.M[unspecified] X1.A4#4 |
    When the drawing is imported
    Then the device "DS" binds "M" to "Alpha/0x20/A4" on driver pin 4, no direction, asserted high
    And it is reported as missing on "DS"

  @device.invert.kind
  Scenario: an Invert that names a value pin
    Given these symbols too:
      | Ref | Symbol                        | Role   | Appliance | Name    | Invert | Pin.VALUE |
      | SEL | Railroad-Office:PanelSelector | DEVICE | selector  | Arrival | VALUE  | value     |
    And these nets:
      | Net | Pins                      |
      | bus | P1.IOBus X1.IOBus         |
      | v   | SEL.VALUE[output] X1.A5#5 |
    When the drawing is imported
    Then the device "SEL" binds "VALUE" to "Alpha/0x20/A5" on driver pin 5, input, with no sense
    And it is reported as an error on "SEL"

  Scenario: a JMRI mast device stands in for the mast it names
    Given these symbols too:
      | Ref | Symbol                              | Role   | Appliance | Name   | Address | JMRI.SignalSystem |
      | MJ  | Railroad-HardwareIO:Device-Mast-JMRI | DEVICE | mast      | 778NAB | 101     | SPTCO-1969        |
    And these nets:
      | Net | Pins                                       |
      | bus | P1.IOBus X1.IOBus MJ.IOBus[passive]#1      |
    When the drawing is imported
    Then the device "MJ" is a device of interlocking "X"
    And the device "MJ" binds "IOBus" to "Alpha/SIGNALMAST.778NAB/IOBus" on driver pin 1, output, with no sense
    And the device "MJ" is written with Address "101"
    And nothing is reported on "MJ"
