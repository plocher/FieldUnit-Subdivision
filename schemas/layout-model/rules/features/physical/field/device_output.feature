Feature: Only the interlocking that owns an appliance drives it
  Every demand is an input to the vital logic of the interlocking that owns the appliance, and only that logic drives the appliance (ADR 0017 decision 3).
  A binding states its direction: the logic drives an output (a switch machine, a lock, a head, a lamp) and reads an input (a lever, a key, a sensor, point detection, occupancy).
  An interlocking's device output driven by a processor that does not run that interlocking is an error: something goes behind the code line's back.
  A demand bound anywhere is never this error: a crew's lever may be read by another interlocking's hardware.

  Background:
    Given interlocking "X" runs on processor "Alpha"
    And interlocking "Y" runs on processor "Beta"
    And interlocking "X" has these appliances:
      | Name   | Appliance | Style   | Kind       |
      | 3      | switch    | powered |            |
      | 778NAB | mast      | double  | CONTROLLED |
    And interlocking "X" has these devices:
      | Name   | Appliance | Style  |
      | 3      | switch    |        |
      | 1L     | lamp      |        |
      | 3L     | lever     | switch |

  @device.output
  Scenario: a switch machine driven by its own interlocking's processor
    Given device "3" of interlocking "X" drives "M" through "Alpha/0x20/A0"
    When the layout is derived
    Then it is not reported

  @device.output
  Scenario: a switch machine driven by another interlocking's processor
    Given device "3" of interlocking "X" drives "M" through "Beta/0x20/A0"
    When the layout is derived
    Then it is reported as an error on "Beta"

  @device.output
  Scenario: a lamp driven by another interlocking's processor
    Given device "1L" of interlocking "X" drives "LAMP" through "Beta/0x21/A0"
    When the layout is derived
    Then it is reported as an error on "Beta"

  @device.output
  Scenario: a switch's point detection read by another interlocking's processor
    Given device "3" of interlocking "X" drives "M" through "Alpha/0x20/A0"
    And device "3" of interlocking "X" reads "N" through "Beta/0x20/A1"
    When the layout is derived
    Then it is not reported

  @device.output
  Scenario: a crew's lever read by another interlocking's processor
    Given device "3L" of interlocking "X" reads "NWS" through "Beta/0x20/A2"
    When the layout is derived
    Then it is not reported

  @device.output
  Scenario: a binding that states no direction is not judged
    Given field mast device "778NAB" of interlocking "X" binds "A" to "Beta/SIGNALMAST.778NAB/IND"
    When the layout is derived
    Then it is not reported
