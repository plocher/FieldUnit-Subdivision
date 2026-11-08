Feature: The faces of a train order board
  The field device of a train order board has one unit for each face: N or W, S or E.
  A board with one face has one unit.
  Each unit has the inputs STOP, SLOW and CALLON and gives its face's indication to a head.
  Nothing asserted is CLEAR. SLOW is APPROACH. CALLON is RESTRICTING.
  The most restrictive asserted input wins. From most to least restrictive: STOP, CALLON, SLOW.
  The control is local. No code line carries it.
  A face can show CLEAR and the word of each input its wires bring it.

  Background:
    Given the timetable has station "Gilroy"
    And interlocking "Gilroy" has these appliances:
      | Name   | Appliance   | Station | relations.station |
      | Gilroy | train_order | Gilroy  | Gilroy            |

  Scenario: a board with two faces
    Given train order device "Gilroy" has units for the faces "N, S"
    When the layout is derived
    Then "Gilroy" has faces "N, S"
    And the "N" face of "Gilroy" serves the direction "LEFT"
    And the "S" face of "Gilroy" serves the direction "RIGHT"

  Scenario: a board with one face
    Given train order device "Gilroy" has units for the faces "W"
    When the layout is derived
    Then "Gilroy" has faces "W"
    And the "W" face of "Gilroy" serves the direction "LEFT"

  @train_order.device
  Scenario: a board with no field device
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.face
  Scenario: a face that names no direction
    Given train order device "Gilroy" has units for the faces "A"
    When the layout is derived
    Then it is reported as an error on "Gilroy"

  @train_order.face
  Scenario: a face two devices both state
    Given train order device "Gilroy" has units for the faces "N"
    And train order device "Gilroy" has units for the faces "N"
    When the layout is derived
    Then it is reported as an error on "Gilroy"

  Scenario: a face shows what its wired inputs can ask for
    Given train order device "Gilroy" has units for the faces "N"
    And the "N" face of "Gilroy" wires the inputs "STOP, SLOW"
    When the layout is derived
    Then the "N" face of "Gilroy" can show "APPROACH, CLEAR, STOP"

  Scenario: a face with no input wired shows CLEAR
    Given train order device "Gilroy" has units for the faces "N"
    When the layout is derived
    Then the "N" face of "Gilroy" can show "CLEAR"

  Scenario Outline: what a face shows
    Given train order device "Gilroy" has units for the faces "N"
    And the "N" face of "Gilroy" has <inputs> asserted
    Then the "N" face of "Gilroy" shows "<indication>"

    Examples:
      | inputs          | indication  |
      | nothing         | CLEAR       |
      | SLOW            | APPROACH    |
      | CALLON          | RESTRICTING |
      | STOP            | STOP        |
      | STOP and SLOW   | STOP        |
      | STOP and CALLON | STOP        |
      | SLOW and CALLON | RESTRICTING |
