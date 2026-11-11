Feature: A joint declared a regime boundary, as drawn
  A joint symbol that carries the field RegimeBoundary = yes is a regime boundary (the owner,
  2026-11-11). The field is written into the joint row's given as drawn, for any joint Kind; the
  symbol's name is never read. What the boundary does to regimes is the model rules'.
  (ADR 0013 §7.1)

  Scenario: the field is written as drawn
    Given this drawing of interlocking "X":
      | Ref | Symbol                                   | Role      | Kind          | RegimeBoundary | Appliance     | Name | CP Name |
      | H1  | Railroad-Trackplan:House                 | STRUCTURE | CONTROL_POINT |                |               |      | East    |
      | TC1 | Railroad-Trackplan:Track Circuit         | APPLIANCE |               |                | track_circuit | 1NAT |         |
      | J1  | Railroad-Trackplan:IRJ Authority Boundry | TRACK     | IRJ           | yes            |               |      |         |
      | J2  | Railroad-Trackplan:IRJ                   | TRACK     | IRJ           |                |               |      |         |
    And these nets:
      | Net | Pins             |
      | a   | TC1.TC J1.A J2.B |
    When the drawing is imported
    Then the row "J1" is written with Kind "IRJ"
    And the row "J1" is written with RegimeBoundary "yes"
    And the row "J2" is written with Kind "IRJ"
