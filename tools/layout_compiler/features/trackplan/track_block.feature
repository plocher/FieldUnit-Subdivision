Feature: Block track across sheets, as drawn
  A track net is read across sheets: the hierarchical label that continues a run is netlist
  connectivity, so no pairing step is needed. Each side names the other sheet's pins by that
  sheet's interlocking: a marker by its qualified name, an unnamed row by its id. (ADR 0013 §7.1)

  Scenario: 834T drawn on Y's sheet reaches X's double joint through the label
    Given this drawing of interlocking "X":
      | Ref | Symbol                                           | Role      | Kind          | Appliance     | Style  | Name  | CP Name |
      | H1  | Railroad-Trackplan:House                         | STRUCTURE | CONTROL_POINT |               |        |       | East    |
      | J1  | Railroad-Trackplan:IRJ-Signals                   | TRACK     | IRJ_SIGNALS   |               |        |       |         |
      | M1  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single | 834NA |         |
      | M2  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE    | mast          | single | 834SA |         |
      | TC1 | Railroad-Trackplan:Track Circuit                 | APPLIANCE |               | track_circuit |        | 836T  |         |
    And this drawing of interlocking "Y":
      | Ref | Symbol                           | Role      | Kind          | Appliance     | Style | Name | CP Name |
      | H2  | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |               |       |      | West    |
      | J2  | Railroad-Trackplan:IRJ           | TRACK     | IRJ           |               |       |      |         |
      | TC2 | Railroad-Trackplan:Track Circuit | APPLIANCE |               | track_circuit |       | 834T |         |
    And these nets:
      | Net | Pins                  |
      | ToX | J1.A TC2.TC J2.B      |
      | b   | J1.B TC1.TC           |
      | sa  | J1.SIGNAL_A M1.SIGNAL |
      | sb  | J1.SIGNAL_B M2.SIGNAL |
    When the drawing is imported
    Then the row "J1" names "Y:834T.TC" on side A
    And the row "J1" names "J2.B" on side A
    And "834T" names "J1.A" on side TC
    And the row "J2" names "J1.A" on side B
    And the row "J1" names "X:836T.TC" on side B
