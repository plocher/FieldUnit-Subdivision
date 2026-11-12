Feature: An encoded driver is keyed by what its wires state
  An encoded driver (a JMRI object) has no address of its own. Its key is its object class and the device it serves.
  A nameless head or train order lever serves under the mast pin its IND wire reaches, not under the mast alone.
  The functions in a key come from the pin names alone. A driver pin named like the device pin it lands on serves that function by its own definition and adds nothing.
  A driver pin named otherwise reads the function it is wired to and takes the device pin's name as a suffix.
  A SignalMast on a mast stands in for positions: it carries the positions its net reaches unless that is every one.
  A hand-written Address is not needed for any of this.
  Two symbols at one key are one object only when they are a Turnout's command and its feedback. Anything else at one key is an error.

  Background:
    Given this drawing of interlocking "X":
      | Ref  | Symbol                                       | Role     | Appliance        | Style       | IC        | Kind       | Address | Name   | Station | Pin.E      | Pin.W      | Pin.STOP | Pin.SLOW | Pin.IND    | Pin.APP    | Pin.A      | Pin.B      | Pin.OCC |
      | DM1  | Railroad-Field:Device-TrainOrder-Mast-Double | DEVICE   | train_order_mast |             |           |            |         | Gilroy |         | indication | indication |          |          |            |            |            |            |         |
      | LE   | Railroad-Field:Local-TrainOrder              | DEVICE   | lever            | train_order |           |            |         |        |         |            |            | binary   | binary   |            |            |            |            |         |
      | LW   | Railroad-Field:Local-TrainOrder              | DEVICE   | lever            | train_order |           |            |         |        |         |            |            | binary   | binary   |            |            |            |            |         |
      | HE   | Railroad-Field:Device-Head-Semaphore-UQ3     | DEVICE   | head             | UQ3         |           |            |         |        |         |            |            |          |          | indication | indication |            |            |         |
      | HW   | Railroad-Field:Device-Head-Semaphore-UQ3     | DEVICE   | head             | UQ3         |           |            |         |        |         |            |            |          |          | indication | indication |            |            |         |
      | DM2  | Railroad-Field:Device-Mast-Double            | DEVICE   | mast             |             |           |            |         | 778NAB |         |            |            |          |          |            |            | indication | indication |         |
      | TC1  | Railroad-Field:Device-TC                     | DEVICE   | track_circuit    |             |           |            |         | 01T    |         |            |            |          |          |            |            |            |            | binary  |
      | SES  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |               |             | MQTT-JMRI | SENSOR     |         |        |         |            |            |          |          |            |            |            |            |         |
      | SEW  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |               |             | MQTT-JMRI | SENSOR     |         |        |         |            |            |          |          |            |            |            |            |         |
      | SWS  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |               |             | MQTT-JMRI | SENSOR     |         |        |         |            |            |          |          |            |            |            |            |         |
      | SWW  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |               |             | MQTT-JMRI | SENSOR     |         |        |         |            |            |          |          |            |            |            |            |         |
      | ME   | Railroad-HardwareIO:Driver-JMRI-SignalMast   | IODRIVER |                  |             | MQTT-JMRI | SIGNALMAST |         |        |         |            |            |          |          |            |            |            |            |         |
      | MW   | Railroad-HardwareIO:Driver-JMRI-SignalMast   | IODRIVER |                  |             | MQTT-JMRI | SIGNALMAST |         |        |         |            |            |          |          |            |            |            |            |         |
      | MM   | Railroad-HardwareIO:Driver-JMRI-SignalMast   | IODRIVER |                  |             | MQTT-JMRI | SIGNALMAST |         |        |         |            |            |          |          |            |            |            |            |         |
      | ST   | Railroad-HardwareIO:Driver-JMRI-Sensor       | IODRIVER |                  |             | MQTT-JMRI | SENSOR     |         |        |         |            |            |          |          |            |            |            |            |         |

  Scenario: Gilroy's double train order mast with two levers and two heads
    Given these nets:
      | Net | Pins                                                         |
      | bus | P1.IOBus SES.IOBus SEW.IOBus SWS.IOBus SWW.IOBus ME.IOBus MW.IOBus |
      | e   | DM1.E LE.IND HE.IND                                          |
      | w   | DM1.W LW.IND HW.IND                                          |
      | es  | LE.~{STOP} SES.S                                             |
      | ew  | LE.~{SLOW} SEW.S                                             |
      | ws  | LW.~{STOP} SWS.S                                             |
      | ww  | LW.~{SLOW} SWW.S                                             |
      | he  | HE.APP ME.IND                                                |
      | hw  | HW.APP MW.IND                                                |
    When the drawing is imported
    Then processor "Alpha" has the drivers "SENSOR.Gilroy.E.STOP, SENSOR.Gilroy.E.SLOW, SENSOR.Gilroy.W.STOP, SENSOR.Gilroy.W.SLOW, SIGNALMAST.Gilroy.E, SIGNALMAST.Gilroy.W"
    And the driver "SES" is keyed "SENSOR.Gilroy.E.STOP"
    And the driver "ME" is keyed "SIGNALMAST.Gilroy.E"
    And no driver is written with an Address
    And the lever "LE" binds "STOP" to "Alpha/SENSOR.Gilroy.E.STOP/S"

  Scenario: a whole-mast consumer on every position keeps the mast's key
    Given these nets:
      | Net | Pins                   |
      | bus | P1.IOBus MM.IOBus      |
      | ab  | DM2.A DM2.B MM.IND     |
    When the drawing is imported
    Then the driver "MM" is keyed "SIGNALMAST.778NAB"

  Scenario: a consumer on one position of a double mast carries that position
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus MM.IOBus |
      | a   | DM2.A MM.IND      |
    When the drawing is imported
    Then the driver "MM" is keyed "SIGNALMAST.778NAB.A"

  Scenario: a sensor reads the function it is wired to
    Given these nets:
      | Net | Pins              |
      | bus | P1.IOBus ST.IOBus |
      | occ | TC1.~{OCC} ST.S   |
    When the drawing is imported
    Then the driver "ST" is keyed "SENSOR.01T.OCC"

  Scenario: a named lock lever with one sensor per function pin
    Given these symbols too:
      | Ref | Symbol                                          | Role     | Appliance | Style | IC        | Kind   | Name | Pin.WLK | Pin.WLQ | Pin.WLQK |
      | LL  | Railroad-Field:Local-Lock                       | DEVICE   | lever     | lock  |           |        | 777  | binary  | binary  | binary   |
      | SK  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |           |       | MQTT-JMRI | SENSOR |      |         |         |          |
      | SQ  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |           |       | MQTT-JMRI | SENSOR |      |         |         |          |
      | SQK | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback | IODRIVER |           |       | MQTT-JMRI | SENSOR |      |         |         |          |
    And these nets:
      | Net | Pins                                      |
      | bus | P1.IOBus SK.IOBus SQ.IOBus SQK.IOBus      |
      | k   | LL.~{WLK} SK.S                            |
      | q   | LL.~{WLQ} SQ.S                            |
      | qk  | LL.~{WLQK} SQK.S                          |
    When the drawing is imported
    Then processor "Alpha" has the drivers "SENSOR.777.WLK, SENSOR.777.WLQ, SENSOR.777.WLQK"
    And the driver "SQK" is keyed "SENSOR.777.WLQK"

  Scenario: a driver pin named like the device pin serves that function and adds nothing
    Given these symbols too:
      | Ref | Symbol                                           | Role     | Appliance | IC        | Kind    | Name | Pin.M  | Pin.N  | Pin.R  | Pin.OCC |
      | SW  | Railroad-Field:Device-Switch-OS                  | DEVICE   | switch    |           |         | 777  | binary | binary | binary | binary  |
      | TC  | Railroad-HardwareIO:Driver-JMRI-Turnout          | IODRIVER |           | MQTT-JMRI | TURNOUT |      |        |        |        |         |
      | TF  | Railroad-HardwareIO:Driver-JMRI-Turnout-Feedback | IODRIVER |           | MQTT-JMRI | TURNOUT |      |        |        |        |         |
      | SO  | Railroad-HardwareIO:Driver-JMRI-Sensor-Feedback  | IODRIVER |           | MQTT-JMRI | SENSOR  |      |        |        |        |         |
    And these nets:
      | Net | Pins                               |
      | bus | P1.IOBus TC.IOBus TF.IOBus SO.IOBus |
      | m   | SW.M TC.M                          |
      | n   | SW.~{N} TF.~{N}                    |
      | r   | SW.~{R} TF.~{R}                    |
      | occ | SW.~{OCC} SO.S                     |
    When the drawing is imported
    Then processor "Alpha" has the drivers "TURNOUT.777, SENSOR.777.OCC"
    And the driver "TURNOUT.777" on "Alpha" is drawn by "TC, TF"

  @driver.duplicate
  Scenario: two sensors on one lever pin
    Given these nets:
      | Net | Pins                        |
      | bus | P1.IOBus SES.IOBus SEW.IOBus |
      | e   | DM1.E LE.IND                |
      | es  | LE.~{STOP} SES.S SEW.S      |
    When the drawing is imported
    Then it is reported as an error on "SEW"

  @driver.duplicate
  Scenario: two mast consumers on one head
    Given these nets:
      | Net | Pins                      |
      | bus | P1.IOBus ME.IOBus MW.IOBus |
      | e   | DM1.E HE.IND              |
      | he  | HE.APP ME.IND MW.IND      |
    When the drawing is imported
    Then it is reported as an error on "MW"

  @driver.duplicate
  Scenario: a Turnout's command and feedback are one object
    Given these symbols too:
      | Ref | Symbol                                        | Role     | Appliance | IC        | Kind    | Name | Pin.M  | Pin.N  | Pin.R  |
      | SW  | Railroad-Field:Device-Switch                  | DEVICE   | switch    |           |         | 777  | binary | binary | binary |
      | TC  | Railroad-HardwareIO:Driver-JMRI-Turnout       | IODRIVER |           | MQTT-JMRI | TURNOUT |      |        |        |        |
      | TF  | Railroad-HardwareIO:Driver-JMRI-Turnout-Feedback | IODRIVER |           | MQTT-JMRI | TURNOUT |      |        |        |        |
    And these nets:
      | Net | Pins                      |
      | bus | P1.IOBus TC.IOBus TF.IOBus |
      | m   | SW.M TC.M                 |
      | n   | SW.~{N} TF.~{N}           |
      | r   | SW.~{R} TF.~{R}           |
    When the drawing is imported
    Then the driver "TC" is keyed "TURNOUT.777"
    And the driver "TURNOUT.777" on "Alpha" is drawn by "TC, TF"
    And it is not reported
