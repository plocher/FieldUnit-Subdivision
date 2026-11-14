Feature: A binding states the facts of the wire it is drawn as
  A device pin wired to a driver pin is a binding. Its route names the bus owner, the address and the driver pin.
  It also states the driver pin's number, as the driver symbol has it. What the number means on the chip is the driver's knowledge.
  Its direction comes from the device pin's electrical type. The logic drives a pin the device takes in (output) and reads a pin the device puts out (input). A driver has no direction of its own.
  Its sense is the asserted level: low for a pin drawn ~{X}, high for a plain name, and the other one when the device's Invert names the pin.
  A device pin whose type states no direction (passive, bidirectional, unspecified) is reported as missing.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                 | Role     | Appliance | IC      | Address | Name   | Invert |
      | X1  | Railroad-HardwareIO:Driver-I2C-MAX7313 | IODRIVER |           | MAX7313 | 0x20    |        |        |
      | DS  | Railroad-Field:Device-Switch-OS        | DEVICE   | switch    |         |         | 3      |        |
      | DL  | Railroad-Field:Device-Lamp             | DEVICE   | lamp      |         |         | 1L     | LAMP   |
      | DM  | Railroad-Field:Device-Mast-Dwarf       | DEVICE   | mast      |         |         | 2NA    |        |

  Scenario: a switch machine and its occupancy
    Given these nets:
      | Net | Pins                    |
      | bus | P1.IOBus X1.IOBus       |
      | m   | DS.M[input] X1.A1#1     |
      | occ | DS.~{OCC}[output] X1.B1#9 |
    When the drawing is imported
    Then the device "DS" binds "M" to "Alpha/0x20/A1" on driver pin 1, output, asserted high
    And the device "DS" binds "OCC" to "Alpha/0x20/B1" on driver pin 9, input, asserted low

  Scenario: a lamp whose Invert names its pin
    Given these nets:
      | Net | Pins                     |
      | bus | P1.IOBus X1.IOBus        |
      | l   | DL.~{LAMP}[input] X1.A2#2 |
    When the drawing is imported
    Then the device "DL" binds "LAMP" to "Alpha/0x20/A2" on driver pin 2, output, asserted high

  @binding.direction
  Scenario: a mast's passive position pin bound to a driver
    Given these nets:
      | Net | Pins                 |
      | bus | P1.IOBus X1.IOBus    |
      | a   | DM.A[passive] X1.A3#3 |
    When the drawing is imported
    Then the device "DM" binds "A" to "Alpha/0x20/A3" on driver pin 3, no direction, asserted high
    And it is reported as missing on "DM"
