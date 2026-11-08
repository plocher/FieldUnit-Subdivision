Feature: The units of a train order device
  The field device of a train order board has one unit for each face, named for it: N or W, S or E.
  The board has the faces whose units are wired.
  A face's STOP, SLOW and CALLON bind to the driver pins their wires reach. Its IND is wired to the head of its face.
  A wired pin whose unit has no name, or a name that is no face, is an error: the face is unknown.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                 | Role      | Appliance   | IC      | Address | Name   | Station |
      | TO1 | Railroad-Trackplan:Train Order Mast    | APPLIANCE | train_order |         |         | Gilroy | Gilroy  |
      | D1  | Railroad-Field:Device-TrainOrder       | DEVICE    | train_order |         |         | Gilroy |         |
      | X1  | Railroad-HardwareIO:Driver-I2C-MAX7311 | IODRIVER  |             | MAX7311 | 0x20    |        |         |

  Scenario: a device with two units wired
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus X1.IOBus |
      | ns  | D1.N.STOP X1.A0   |
      | nc  | D1.N.CALLON X1.A1 |
      | ss  | D1.S.STOP X1.A2   |
    When the drawing is imported
    Then "Gilroy" has faces "N, S"
    And face "N" of "Gilroy" binds "STOP" to "Alpha/0x20/A0"
    And face "N" of "Gilroy" binds "CALLON" to "Alpha/0x20/A1"
    And face "S" of "Gilroy" binds "STOP" to "Alpha/0x20/A2"

  Scenario: a device with one unit wired
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus X1.IOBus |
      | ws  | D1.W.STOP X1.A0   |
    When the drawing is imported
    Then "Gilroy" has faces "W"

  @train_order.unit
  Scenario: a unit that names no face
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus X1.IOBus |
      | as  | D1.A.STOP X1.A0   |
    When the drawing is imported
    Then it is reported as an error on "D1"

  @train_order.unit
  Scenario: a pin in a unit with no name
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus X1.IOBus |
      | s   | D1.STOP X1.A0     |
    When the drawing is imported
    Then it is reported as an error on "D1"
