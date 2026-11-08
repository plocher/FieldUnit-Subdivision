Feature: What a mast is, as drawn
  A mast's Kind is a field of its symbol, written as given. A grade or restricting plate is a
  POLICY symbol whose pin To sits on the mast's SIGNAL net: its row states that mast and no
  track side. A plate on anything else states no mast; that it then has none, and that the
  mast is PERMISSIVE, are the model's checks. (ADR 0013 §5)

  Background: two automatic masts back to back on an IRJ-Signals joint
    Given this drawing of interlocking "X":
      | Ref | Symbol                                        | Role      | Kind          | Appliance     | Style  | Name  | CP Name |
      | H1  | Railroad-Trackplan:House                      | STRUCTURE | CONTROL_POINT |               |        |       | East    |
      | TC1 | Railroad-Trackplan:Track Circuit              | APPLIANCE |               | track_circuit |        | 832T  |         |
      | TC2 | Railroad-Trackplan:Track Circuit              | APPLIANCE |               | track_circuit |        | 834T  |         |
      | J1  | Railroad-Trackplan:IRJ-Signals                | TRACK     | IRJ_SIGNALS   |               |        |       |         |
      | M1  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE | mast          | single | 832NA |         |
      | M2  | Railroad-Trackplan:Signal Mast Single PERMISSIVE | APPLIANCE | PERMISSIVE | mast          | single | 832SA |         |
      | PL1 | Railroad-Trackplan:Signal Mast Plate-G        | POLICY    | RULE_290_G    |               |        |       |         |

  Scenario: a mast's Kind is written as drawn
    Given these nets:
      | Net | Pins                   |
      | a   | J1.A TC1.TC            |
      | b   | J1.B TC2.TC            |
      | sa  | J1.SIGNAL_A M1.SIGNAL  |
      | sb  | J1.SIGNAL_B M2.SIGNAL  |
    When the drawing is imported
    Then "832NA" is written with Kind "PERMISSIVE"

  Scenario: a plate on a mast's SIGNAL net
    Given these nets:
      | Net | Pins                          |
      | a   | J1.A TC1.TC                   |
      | b   | J1.B TC2.TC                   |
      | sa  | J1.SIGNAL_A M1.SIGNAL         |
      | sb  | J1.SIGNAL_B M2.SIGNAL PL1.To  |
    When the drawing is imported
    Then the row "PL1" states the relation mast "X:832SA"
    And the row "PL1" states no relation track

  Scenario: a plate on the track states no mast
    Given these nets:
      | Net | Pins                   |
      | a   | J1.A TC1.TC            |
      | b   | J1.B TC2.TC PL1.To     |
      | sa  | J1.SIGNAL_A M1.SIGNAL  |
      | sb  | J1.SIGNAL_B M2.SIGNAL  |
    When the drawing is imported
    Then the row "PL1" states no relation mast
    And the row "PL1" states no relation track
