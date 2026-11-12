Feature: A trackplan symbol's interlocking, as drawn
  A symbol with Role TRACK, APPLIANCE or POLICY is placed by its CP Name when it names an
  interlocking or one of its houses, else by its sheet, the nearest interlocking at or above,
  else by its track net when the nets on its track pins reach exactly one interlocking's track;
  a symbol none of these places is reported, never dropped. (the owner, 2026-11-11; sheet scope
  is a default, 2026-10-28)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role      | Kind          | Appliance     | Name | CP Name |
      | H1  | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |               |      | East    |
      | TC1 | Railroad-Trackplan:Track Circuit | APPLIANCE |               | track_circuit | 1NAT |         |
      | J1  | Railroad-Trackplan:IRJ           | TRACK     | IRJ           |               |      |         |

  Scenario: a NextCP on the sheet above wired to one interlocking's track is that interlocking's
    Given these symbols on the sheet above:
      | Ref | Symbol                              | Role  | Kind    | Interlocking | Style      |
      | N1  | Railroad-Trackplan:NextCP Not Modeled | TRACK | NEXT_CP | Lick         | off_layout |
    And these nets:
      | Net | Pins             |
      | NMT | TC1.TC J1.B N1.To |
    When the drawing is imported
    Then the row "N1" is in interlocking "X"
    And the row "N1" is written with Interlocking "Lick"
    And the row "N1" names "X:1NAT.TC" on side track

  @trackplan.unit
  Scenario: a NextCP on the sheet above wired to no interlocking's track belongs to none
    Given these symbols on the sheet above:
      | Ref | Symbol                              | Role  | Kind    | Interlocking |
      | N1  | Railroad-Trackplan:NextCP Not Modeled | TRACK | NEXT_CP | Lick         |
      | J9  | Railroad-Trackplan:IRJ                | TRACK | IRJ     |              |
    And these nets:
      | Net | Pins      |
      | t   | TC1.TC J1.B |
      | n   | N1.To J9.A  |
    When the drawing is imported
    Then it is reported as missing on "N1"
    And it is reported as missing on "J9"
    And no row is written for "N1"

  Scenario: a track circuit on another interlocking's sheet with the CP Name of a house of X is X's
    Given this drawing of interlocking "Y":
      | Ref | Symbol                           | Role      | Kind          | Appliance     | Name | CP Name |
      | H2  | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |               |      | West    |
      | TC2 | Railroad-Trackplan:Track Circuit | APPLIANCE |               | track_circuit | 2NAT | East    |
    And these nets:
      | Net | Pins        |
      | t   | TC1.TC J1.B |
    When the drawing is imported
    Then "2NAT" is in interlocking "X"
