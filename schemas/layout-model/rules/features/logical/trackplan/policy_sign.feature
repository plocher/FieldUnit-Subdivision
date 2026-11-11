Feature: A sign states its rule for the track it stands on
  A policy sign states its Kind and Direction as given and the track it stands on. A GCOR Rule
  9.14 sign's LEFT or RIGHT is the current of traffic: the lever direction of the signals that
  govern with it. A 9.14 sign inside interlocking limits states the current of traffic on that
  track and nothing more; it is a direction fact, not a regime, and may share a piece with one.
  The regime of a piece of track (CTC, TWC, DTC, yard limits, other than main track) is a GCOR
  Rule marker on it, since no arrangement of signals implies it; its extent is derived as a track
  circuit's is. The unit is the joint-bounded piece. A piece's regime is the marker on it; else
  what it inherits across a joint from the piece beside it, so one marker covers a run cut into
  blocks or circuits, and a siding inside CTC limits is CTC. Interlocking track inherits like any
  other track: a control point can be under a control operator without being under the CTC
  rulebook (GCOR 6.4.2, 9.12.2), so which regime an interlocking lies under is a fact the model
  tells, never an error. A regime boundary is a plain joint with a marker on each side; the track beyond it
  is in the model under its own regime. Errors, not guesses. That the signs of one block agree with
  each other and with its masts is the blocks library's. (ADR 0013 §7.1, §8, decision 3)

  Background:
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name | Appliance     |
      | 1NAT | track_circuit |

  @policy.direction
  Scenario: a 9.14 sign states the current of traffic on its track and nothing more
    Given interlocking "X" has these policies:
      | Id | Kind           | Direction |
      | R1 | GCOR_RULE_9_14 | RIGHT     |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | t    | R1.track 1NAT.TC |
    When the layout is derived
    Then sign "R1" stands on circuit "X:1NAT"
    And it is not reported

  @policy.direction
  Scenario: a 9.14 sign that states no current of traffic
    Given interlocking "X" has these policies:
      | Id | Kind           | Direction |
      | R1 | GCOR_RULE_9_14 | BOTH      |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | t    | R1.track 1NAT.TC |
    When the layout is derived
    Then it is reported as missing on "R1"

  @policy.track
  Scenario: a sign on no track
    Given interlocking "X" has these policies:
      | Id | Kind           | Direction |
      | R1 | GCOR_RULE_9_14 | RIGHT     |
    When the layout is derived
    Then it is reported as missing on "R1"

  @regime.conflict
  Scenario: a regime marker's extent across plain joints: the Beet Loader rejoins two interlockings
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC  | CP Name |
      | 1    | switch    | local | 1T1 | East    |
    And interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |
    And interlocking "X" has these ends:
      | Id | Kind     | Name          |
      | E1 | INDUSTRY | BeetLoader1 |
      | E2 | INDUSTRY | BeetLoader2 |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_10 |
      | R2 | GCOR_RULE_14 |
    And interlocking "Y" has house "West"
    And interlocking "Y" has these appliances:
      | Name | Appliance     | Style | TC  | CP Name |
      | 1    | switch        | local | 1T1 | West    |
      | 02T  | track_circuit |       |     |         |
    And interlocking "Y" has these joints:
      | Id | Kind |
      | J2 | IRJ  |
    And interlocking "Y" has these policies:
      | Id | Kind         |
      | R3 | GCOR_RULE_10 |
      | R4 | GCOR_RULE_14 |
    And interlocking "X" has these wires:
      | Wire | Pins                          |
      | c    | J1.B 1NAT.TC R1.track         |
      | b    | J1.A R2.track 1.C             |
      | n    | 1.N BeetLoader2.EoT Y:1.N   |
      | r    | 1.R BeetLoader1.EoT Y:1.R   |
    And interlocking "Y" has these wires:
      | Wire | Pins                          |
      | c    | J2.B 02T.TC R3.track          |
      | b    | J2.A R4.track 1.C             |
      | n    | 1.N X:BeetLoader2.EoT X:1.N |
      | r    | 1.R X:BeetLoader1.EoT X:1.R |
    When the layout is derived
    Then the piece "X:1T1" is under regime "GCOR_RULE_14" by a marker
    And the piece "Y:1T1" is under regime "GCOR_RULE_14" by a marker
    And the piece "X:1NAT" is under regime "GCOR_RULE_10" by a marker
    And the piece "Y:02T" is under regime "GCOR_RULE_10" by a marker
    And it is not reported

  @regime.none
  Scenario: a one-ended lead beyond the boundary is under its own regime
    Given interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |
    And interlocking "X" has these ends:
      | Id | Kind     | Name            |
      | E1 | INDUSTRY | GilroyIndustry |
    And interlocking "X" has these policies:
      | Id | Kind           |
      | R1 | GCOR_RULE_10   |
      | R2 | GCOR_RULE_6_28 |
    And interlocking "X" has these wires:
      | Wire | Pins                           |
      | c    | J1.B 1NAT.TC R1.track          |
      | d    | J1.A R2.track GilroyIndustry.EoT |
    When the layout is derived
    Then the piece "X:GilroyIndustry" is under regime "GCOR_RULE_6_28" by a marker
    And the piece "X:1NAT" is under regime "GCOR_RULE_10" by a marker
    And it is not reported

  @regime.none
  Scenario: yard limits on a bumper track
    Given interlocking "X" has these ends:
      | Id | Kind   |
      | B1 | BUMPER |
    And interlocking "X" has these policies:
      | Id | Kind           |
      | R1 | GCOR_RULE_6_13 |
    And interlocking "X" has these wires:
      | Wire | Pins                    |
      | y    | B1.EoT 1NAT.TC R1.track |
    When the layout is derived
    Then the piece "X:1NAT" is under regime "GCOR_RULE_6_13" by a marker
    And it is not reported

  @regime.ambiguous
  Scenario: one marker covers the control point and the track beside it, across the joints
    Given interlocking "X" has these appliances:
      | Name | Appliance     | Style   | TC    | CP Name |
      | 835  | switch        | powered | 835T1 | East    |
      | 2NAT | track_circuit |         |       |         |
    And interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |
      | J2 | IRJ  |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_10 |
    And interlocking "X" has these wires:
      | Wire | Pins                  |
      | c    | 835.C J1.A            |
      | a    | J1.B 1NAT.TC R1.track |
      | n    | 835.N J2.A            |
      | b    | J2.B 2NAT.TC          |
    When the layout is derived
    Then the piece "X:1NAT" is under regime "GCOR_RULE_10" by a marker
    And the piece "X:835T1" is under regime "GCOR_RULE_10" by inheritance
    And the piece "X:2NAT" is under regime "GCOR_RULE_10" by inheritance
    And it is not reported

  @regime.conflict
  Scenario: two regimes on one piece is an error
    Given interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_14 |
      | R2 | GCOR_RULE_16 |
    And interlocking "X" has these wires:
      | Wire | Pins                      |
      | t    | R1.track R2.track 1NAT.TC |
    When the layout is derived
    Then it is reported as an error on "R1"
    And the piece "X:1NAT" is under no regime

  @regime.limits
  Scenario: a lock switch inside the home signal inherits the regime from the track beside it, like any track
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | TC    | CP Name | Kind       |
      | 835   | switch    | lock   | 835T1 | East    |            |
      | 836NA | mast      | single |       | East    | CONTROLLED |
    And interlocking "X" has these joints:
      | Id | Kind       | relations.mast |
      | J1 | IRJ_SIGNAL | X:836NA        |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_10 |
    And interlocking "X" has these wires:
      | Wire | Pins                         |
      | c    | 835.C J1.governed            |
      | a    | J1.approach 1NAT.TC R1.track |
    When the layout is derived
    Then the piece "X:835T1" is under regime "GCOR_RULE_10" by inheritance
    And it is reported as information on "X"

  @regime.limits
  Scenario: a powered switch under yard limits is a fact of the drawing, not a defect
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style   | TC  | CP Name | Kind       |
      | 3     | switch    | powered | 3T1 | East    |            |
      | 840NA | mast      | single  |     | East    | CONTROLLED |
    And interlocking "X" has these joints:
      | Id | Kind       | relations.mast |
      | J1 | IRJ_SIGNAL | X:840NA        |
    And interlocking "X" has these policies:
      | Id | Kind           |
      | R1 | GCOR_RULE_6_13 |
    And interlocking "X" has these wires:
      | Wire | Pins                     |
      | c    | 3.N J1.governed R1.track |
      | a    | J1.approach 1NAT.TC      |
    When the layout is derived
    Then the piece "X:3T1" is under regime "GCOR_RULE_6_13" by a marker
    And the piece "X:1NAT" is under regime "GCOR_RULE_6_13" by inheritance
    And it is reported as information on "X"

  @regime.limits
  Scenario: an interlocking is told which regime its limits lie under
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC    | CP Name |
      | 835  | switch    | powered | 835T1 | East    |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_10 |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | c    | 835.C R1.track   |
    When the layout is derived
    Then it is reported as information on "X"

  @regime.ambiguous
  Scenario: a piece with no marker between two regimes is an error
    Given interlocking "X" has these appliances:
      | Name | Appliance     |
      | 2NAT | track_circuit |
      | 3NAT | track_circuit |
    And interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |
      | J2 | IRJ  |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_14 |
      | R2 | GCOR_RULE_16 |
    And interlocking "X" has these wires:
      | Wire | Pins                  |
      | a    | 1NAT.TC R1.track J1.A |
      | m    | J1.B 2NAT.TC J2.A     |
      | b    | J2.B 3NAT.TC R2.track |
    When the layout is derived
    Then it is reported as an error on "X"
    And the piece "X:2NAT" is under no regime

  @regime.none
  Scenario: a piece with no regime is missing
    Given interlocking "X" has these ends:
      | Id | Kind   |
      | B1 | BUMPER |
    And interlocking "X" has these wires:
      | Wire | Pins           |
      | y    | B1.EoT 1NAT.TC |
    When the layout is derived
    Then it is reported as missing on "X"
    And the piece "X:1NAT" is under no regime

  @regime.absolute
  Scenario: a CTC piece whose head-block signals are absolute is a warning
    Given interlocking "X" has these appliances:
      | Name  | Appliance     | Style  | Kind     |
      | 2NAT  | track_circuit |        |          |
      | 3NAT  | track_circuit |        |          |
      | 832WA | mast          | single | ABSOLUTE |
      | 834EA | mast          | single | ABSOLUTE |
    And interlocking "X" has these joints:
      | Id | Kind       | relations.mast |
      | J1 | IRJ_SIGNAL | X:832WA        |
      | J2 | IRJ_SIGNAL | X:834EA        |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | R1 | GCOR_RULE_10 |
    And interlocking "X" has these wires:
      | Wire | Pins                                        |
      | g    | J1.governed 1NAT.TC R1.track J2.governed    |
      | a    | J1.approach 2NAT.TC                         |
      | b    | J2.approach 3NAT.TC                         |
    When the layout is derived
    Then it is reported as a warning on "R1"
    And the piece "X:1NAT" is under regime "GCOR_RULE_10" by a marker
