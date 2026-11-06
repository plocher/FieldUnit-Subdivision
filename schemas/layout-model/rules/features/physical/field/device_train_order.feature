Feature: The faces of a train order board
  The field device of a train order board has one unit for each face: N or W, S or E.
  A board with one face has one unit.
  Each unit has the inputs STOP, SLOW and CALLON and gives its face's indication to a head.
  Nothing asserted is CLEAR. SLOW is APPROACH. CALLON is RESTRICTING.
  The most restrictive asserted input wins. From most to least restrictive: STOP, CALLON, SLOW.
  The control is local. No code line carries it.

  @pending
  Scenario: a board with two faces
    Given train order device "Gilroy" has units for the faces "N, S"
    When the layout is derived
    Then "Gilroy" has faces "N, S"

  @pending
  Scenario: a board with one face
    Given train order device "Gilroy" has units for the faces "W"
    When the layout is derived
    Then "Gilroy" has faces "W"

  @pending
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
