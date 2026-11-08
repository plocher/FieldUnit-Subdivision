Feature: A joint with a mast on each side, as drawn
  IRJ-Signals is Role TRACK, Kind IRJ_SIGNALS, with pins A, B, SIGNAL_A and SIGNAL_B. The mast
  whose SIGNAL pin is on the SIGNAL_A net governs into side A, the one on SIGNAL_B into side B.
  Nothing is read from rotation or from which mast is drawn first. One pin carries one mast.
  (ADR 0013 §6)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                           | Role      | Kind          | Appliance     | Style  | Name  | CP Name |
      | H1  | Railroad-Trackplan:House                         | STRUCTURE | CONTROL_POINT |               |        |       | East    |
      | TC1 | Railroad-Trackplan:Track Circuit                 | APPLIANCE |               | track_circuit |        | 832T  |         |
      | TC2 | Railroad-Trackplan:Track Circuit                 | APPLIANCE |               | track_circuit |        | 834T  |         |
      | J1  | Railroad-Trackplan:IRJ-Signals                   | TRACK     | IRJ_SIGNALS   |               |        |       |         |
      | M1  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single | 832NA |         |
      | M2  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single | 832SA |         |

  Scenario: a mast on each SIGNAL pin
    Given these nets:
      | Net | Pins                  |
      | a   | J1.A TC1.TC           |
      | b   | J1.B TC2.TC           |
      | sa  | J1.SIGNAL_A M1.SIGNAL |
      | sb  | J1.SIGNAL_B M2.SIGNAL |
    When the drawing is imported
    Then the joint "J1" states the mast "X:832NA" on side A
    And the joint "J1" states the mast "X:832SA" on side B
    And the row "J1" names "X:832T.TC" on side A
    And the row "J1" names "X:834T.TC" on side B

  Scenario: the masts drawn in the other order
    Given these nets:
      | Net | Pins                  |
      | sb  | M2.SIGNAL J1.SIGNAL_B |
      | sa  | M1.SIGNAL J1.SIGNAL_A |
      | b   | TC2.TC J1.B           |
      | a   | TC1.TC J1.A           |
    When the drawing is imported
    Then the joint "J1" states the mast "X:832NA" on side A
    And the joint "J1" states the mast "X:832SA" on side B

  @joint.masts
  Scenario: two masts on one SIGNAL pin
    Given these nets:
      | Net | Pins                            |
      | a   | J1.A TC1.TC                     |
      | b   | J1.B TC2.TC                     |
      | sa  | J1.SIGNAL_A M1.SIGNAL M2.SIGNAL |
    When the drawing is imported
    Then it is reported as an error on "J1"
    And the row "J1" states no relation masts

  Scenario: a SIGNAL pin with no mast
    Given these nets:
      | Net | Pins                  |
      | a   | J1.A TC1.TC           |
      | b   | J1.B TC2.TC           |
      | sa  | J1.SIGNAL_A M1.SIGNAL |
    When the drawing is imported
    Then the joint "J1" states the mast "X:832NA" on side A
    And the joint "J1" states no mast on side B
