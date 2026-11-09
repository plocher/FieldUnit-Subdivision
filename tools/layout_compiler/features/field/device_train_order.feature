Feature: A face of a train order board is a pin of its field mast
  A train order board's field mast device has one passive pin per face: E and W, or N and S, on a double mast; one pin on a single mast.
  A head whose IND is wired to a face pin is that face's head.
  A fascia lever whose IND is wired to the same pin serves that face. Its STOP and SLOW bind to the driver pins their wires reach.
  A lever wired to no face pin is missing its face. A lever or a head wired to two faces is an error.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                       | Role      | Appliance        | Style       | IC      | Address | Name   | Station |
      | TO1 | Railroad-Trackplan:Train Order Mast Double   | APPLIANCE | train_order      | double      |         |         | Gilroy | Gilroy  |
      | DM1 | Railroad-Field:Device-TrainOrder-Mast-Double | DEVICE    | train_order_mast |             |         |         | Gilroy |         |
      | HE  | Railroad-Field:Device-Head-Semaphore-UQ      | DEVICE    | head             | UQ          |         |         |        |         |
      | LE  | Railroad-Field:Local-TrainOrder              | DEVICE    | lever            | train_order |         |         |        |         |
      | X1  | Railroad-HardwareIO:Driver-I2C-MAX7311       | IODRIVER  |                  |             | MAX7311 | 0x20    |        |         |

  Scenario: a head and a lever on one face
    Given these nets:
      | Net | Pins                |
      | bus | P1.IOBus X1.IOBus   |
      | e   | DM1.E HE.IND LE.IND |
      | es  | LE.STOP X1.A0       |
      | ew  | LE.SLOW X1.A1       |
    When the drawing is imported
    Then the head "HE" is on face "E" of "Gilroy"
    And the lever "LE" is on face "E" of "Gilroy"
    And the lever "LE" binds "STOP" to "Alpha/0x20/A0"
    And the lever "LE" binds "SLOW" to "Alpha/0x20/A1"

  @lever.face
  Scenario: a lever wired to no face
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus X1.IOBus |
      | es  | LE.STOP X1.A0     |
    When the drawing is imported
    Then it is reported as missing on "LE"

  @lever.faces
  Scenario: a lever wired to two faces
    Given these nets:
      | Net | Pins               |
      | bus | P1.IOBus X1.IOBus  |
      | ew  | DM1.E DM1.W LE.IND |
    When the drawing is imported
    Then it is reported as an error on "LE"

  @head.masts
  Scenario: a head wired to two faces
    Given these nets:
      | Net | Pins               |
      | ew  | DM1.E DM1.W HE.IND |
    When the drawing is imported
    Then it is reported as an error on "HE"
