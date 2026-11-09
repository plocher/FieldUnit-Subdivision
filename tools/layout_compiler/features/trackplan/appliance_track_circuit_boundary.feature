Feature: A boundary track circuit, as drawn
  The symbol Track Circuit IR Boundary is Appliance track_circuit, Style boundary, with pins A
  and B on the two nets at a joint. Its row states the pins on each side, and each side's other
  pins name it back: it is counted toward both circuits. It has no TC pin and names no circuit.
  Both pins on one net short the joint. (ADR 0013 §10)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                           | Role      | Kind          | Appliance     | Style    | Name  | CP Name |
      | H1  | Railroad-Trackplan:House                         | STRUCTURE | CONTROL_POINT |               |          |       | East    |
      | TC1 | Railroad-Trackplan:Track Circuit                 | APPLIANCE |               | track_circuit |          | 832T  |         |
      | TC2 | Railroad-Trackplan:Track Circuit                 | APPLIANCE |               | track_circuit |          | 834T  |         |
      | TC3 | Railroad-Trackplan:Track Circuit IR Boundary     | APPLIANCE |               | track_circuit | boundary | 833T  |         |
      | J1  | Railroad-Trackplan:IRJ-Signals                   | TRACK     | IRJ_SIGNALS   |               |          |       |         |
      | M1  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single   | 832NA |         |
      | M2  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single   | 832SA |         |

  Scenario: a boundary on the two nets at its joint
    Given these nets:
      | Net | Pins                  |
      | a   | J1.A TC1.TC TC3.A     |
      | b   | J1.B TC2.TC TC3.B     |
      | sa  | J1.SIGNAL_A M1.SIGNAL |
      | sb  | J1.SIGNAL_B M2.SIGNAL |
    When the drawing is imported
    Then "833T" names "X:832T.TC" on side A
    And "833T" names "X:834T.TC" on side B
    And the row "J1" names "X:833T.A" on side A
    And the row "J1" names "X:833T.B" on side B
    And "832T" names "X:833T.A" on side TC

  @track.shorted
  Scenario: both pins of a boundary on one net
    Given these nets:
      | Net | Pins                    |
      | a   | J1.A TC1.TC TC3.A TC3.B |
      | b   | J1.B TC2.TC             |
      | sa  | J1.SIGNAL_A M1.SIGNAL   |
      | sb  | J1.SIGNAL_B M2.SIGNAL   |
    When the drawing is imported
    Then it is reported as an error on "TC3"
