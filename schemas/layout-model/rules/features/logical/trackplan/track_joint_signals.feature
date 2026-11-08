Feature: A joint with a mast on each side
  A joint of Kind IRJ_SIGNALS keeps its sides A and B and states the mast on each side.
  Each mast governs into the side its pin names and approaches over the other side:
  approach and governed are relative to a mast, never to the joint. The joint is the
  signal joint of each of its masts. A signal location is a block boundary: one joint with
  its masts, and the track circuits on each side; a control point is a signal location with
  one side toward the block. (ADR 0013 §6)

  Background: signal location 832, two masts back to back
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name  | Appliance     | Style  | Kind       |
      | 832T  | track_circuit |        |            |
      | 834T  | track_circuit |        |            |
      | 832NA | mast          | single | PERMISSIVE |
      | 832SA | mast          | single | PERMISSIVE |

  Scenario: a mast on each side of the joint
    Given interlocking "X" has these joints:
      | Id | Kind        | relations.masts     |
      | J1 | IRJ_SIGNALS | A=X:832NA B=X:832SA |
    And interlocking "X" has these wires:
      | Wire | Pins         |
      | a    | J1.A 832T.TC |
      | b    | J1.B 834T.TC |
    When the layout is derived
    Then "832NA" governs into "X:832T" and approaches over "X:834T"
    And "832SA" governs into "X:834T" and approaches over "X:832T"
    And joint "J1" has circuit "X:832T" on side A and "X:834T" on side B
    And joint "J1" belongs to no control point

  @mast.joint
  Scenario: a side with no mast leaves that mast on no joint
    Given interlocking "X" has these joints:
      | Id | Kind        | relations.masts |
      | J1 | IRJ_SIGNALS | A=X:832NA       |
    And interlocking "X" has these wires:
      | Wire | Pins         |
      | a    | J1.A 832T.TC |
      | b    | J1.B 834T.TC |
    When the layout is derived
    Then it is reported as missing on "832SA"
    And "832NA" governs into "X:832T" and approaches over "X:834T"
    And "832SA" has no derived circuits

  @mast.joints
  Scenario: one mast on both sides of the joint
    Given interlocking "X" has these joints:
      | Id | Kind        | relations.masts     |
      | J1 | IRJ_SIGNALS | A=X:832NA B=X:832NA |
    And interlocking "X" has these wires:
      | Wire | Pins         |
      | a    | J1.A 832T.TC |
      | b    | J1.B 834T.TC |
    When the layout is derived
    Then it is reported as an error on "832NA"
