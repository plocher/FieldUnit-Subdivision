Feature: A boundary track circuit
  A boundary track circuit (Appliance track_circuit, Style boundary) is a detector at a joint,
  on the two circuits there. The model states which circuits it counts toward: the circuit on
  each of its sides. It names no circuit itself, never splits one and never ends a block; the
  markers on each side name the circuits. (ADR 0013 §10)

  Background: a detector at signal location 832, between 832T and 834T
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name  | Appliance     | Style    | Kind       |
      | 832T  | track_circuit |          |            |
      | 834T  | track_circuit |          |            |
      | 833T  | track_circuit | boundary |            |
      | 832NA | mast          | single   | PERMISSIVE |
      | 832SA | mast          | single   | PERMISSIVE |
    And interlocking "X" has these joints:
      | Id | Kind        | relations.masts     |
      | J1 | IRJ_SIGNALS | A=X:832NA B=X:832SA |

  @circuit.names
  Scenario: a boundary counts toward the circuit on each side and names none
    Given interlocking "X" has these wires:
      | Wire | Pins                |
      | a    | J1.A 832T.TC 833T.A |
      | b    | J1.B 834T.TC 833T.B |
    When the layout is derived
    Then "833T" counts toward "X:832T" on side A and "X:834T" on side B
    And joint "J1" has circuit "X:832T" on side A and "X:834T" on side B
    And it is not reported

  Scenario: a side with no marker is dark, not named for the boundary
    Given interlocking "X" has these wires:
      | Wire | Pins                |
      | a    | J1.A 832T.TC 833T.A |
      | b    | J1.B 833T.B         |
    When the layout is derived
    Then "833T" counts toward "X:832T" on side A and nothing on side B
    And joint "J1" has circuit "X:832T" on side A and dark track on side B
