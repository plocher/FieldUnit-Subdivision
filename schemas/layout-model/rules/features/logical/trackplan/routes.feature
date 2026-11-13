Feature: The routes of a mast
  A route belongs to the mast that displays it (the owner, 2026-11-13). A route runs from a controlled mast, in the
  direction it governs, until the next mast that governs the same movement, or the end of track: a bumper, an
  industry end, or a NextCP edge with no signal beyond (ADR 0012 §5.3). A regime marker is never a limit (the owner,
  2026-11-13): the route passes it, states the regime of each circuit it passes, and the regime may contribute to its
  ceiling (reference data: GCOR 6.13, Yard Limits, contributes RESTRICTING). At a switch entered at C the route takes N or R; entered at N or R it leaves by C. A derail has legs C
  and R only, and a route through it needs it REVERSE. A route is a single path: one position per switch.
  The direction is the movement along the track, never LEFT or RIGHT: the walk follows the track and each mast's
  relations.facing, and LEFT or RIGHT is only the demand word of a signal (written `<signal>(<direction>)` here; the library states the atoms).
  Every term is a static fact (ADR 0012 §5.2): how the terms combine, route locking and signal locking are FieldUnit's.
  Routes are computed on demand from the derived file (tools/railroad/routes.py); nothing is stored.

  Background: interlocking X, two switches and a dependent derail between a signal location and a neighbour
    Given interlocking "Y" has these appliances:
      | Name   | Appliance | Style  | Kind       | CP Name | signal | heads | relations.facing |
      | 816NAB | mast      | double | CONTROLLED | Y       | 816    | A,B   | LEFT             |
    And interlocking "Y" has these joints:
      | Id   | Kind       | CP Name | relations.mast |
      | J816 | IRJ_SIGNAL | Y       | Y:816NAB       |
    And interlocking "X" has these appliances:
      | Name   | Appliance     | Style          | Kind       | TC    | CP Name | signal | heads | relations.facing | IndicationCeiling | relations.switch |
      | 829    | switch        | powered        |            | 829T1 | X       |        |       |                  |                   |                  |
      | 827    | switch        | lock           |            | 827T1 | X       |        |       |                  |                   |                  |
      | 827D   | switch        | derail,powered |            |       | X       |        |       |                  | STOP/RESTRICTING  | X:827            |
      | 830NAB | mast          | double         | CONTROLLED |       | X       | 830    | A,B   | LEFT             |                   |                  |
      | 830SAB | mast          | double         | CONTROLLED |       | X       | 830    | A,B   | RIGHT            |                   |                  |
      | 828SA  | mast          | single         | CONTROLLED |       | X       | 828    | A     | RIGHT            |                   |                  |
      | 828NA  | mast          | dwarf          | CONTROLLED |       | X       | 828    | A     | LEFT             |                   |                  |
      | 832NA  | mast          | single         | PERMISSIVE |       |         | 832    | A     | LEFT             |                   |                  |
      | 832SA  | mast          | single         | PERMISSIVE |       |         | 832    | A     | RIGHT            |                   |                  |
      | 832T   | track_circuit |                |            |       |         |        |       |                  |                   |                  |
      | 834T   | track_circuit |                |            |       |         |        |       |                  |                   |                  |
      | 1NAT   | track_circuit |                |            |       |         |        |       |                  |                   |                  |
      | 2NAT   | track_circuit |                |            |       |         |        |       |                  |                   |                  |
      | 01T    | track_circuit |                |            |       | X       |        |       |                  |                   |                  |
    And interlocking "X" has these joints:
      | Id   | Kind        | CP Name | relations.mast | relations.masts     |
      | J830 | IRJ_SIGNAL  | X       | X:830NAB       |                     |
      | J831 | IRJ_SIGNAL  | X       | X:830SAB       |                     |
      | J828 | IRJ_SIGNAL  | X       | X:828SA        |                     |
      | J829 | IRJ_SIGNAL  | X       | X:828NA        |                     |
      | J832 | IRJ_SIGNALS |         |                | A=X:832NA B=X:832SA |
      | J1   | IRJ         |         |                |                     |
      | J2   | IRJ         |         |                |                     |
    And interlocking "X" has these ends:
      | Id | Kind    |
      | E1 | NEXT_CP |
      | E2 | NEXT_CP |
      | E3 | BUMPER  |
    And interlocking "X" has these policies:
      | Id | Kind         |
      | P1 | GCOR_RULE_10 |
      | P2 | GCOR_RULE_14 |
      | P3 | GCOR_RULE_10 |
    And interlocking "X" has these wires:
      | Wire | Pins                                   |
      | a    | J830.approach 832T.TC J832.A P1.track  |
      | b    | J830.governed 829.C                    |
      | c    | 829.N J1.B                             |
      | d    | J1.A 827.N                             |
      | e    | 829.R J831.governed                    |
      | f    | J831.approach 1NAT.TC E1.track         |
      | g    | 827.C J828.governed                    |
      | h    | J828.approach 2NAT.TC J816.approach    |
      | i    | 827.R 827D.R                           |
      | j    | 827D.C J829.governed                   |
      | k    | J829.approach 01T.TC J2.B P3.track     |
      | l    | J2.A P2.track E3.EoT                   |
      | m    | J832.B 834T.TC E2.track                |
    And interlocking "Y" has these wires:
      | Wire | Pins                                   |
      | a    | J816.approach X:2NAT.TC J828.approach  |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 828  | signal |
      | 830  | signal |
    And the desk has these levers for interlocking "Y":
      | Name | Style  |
      | 816  | signal |

  Scenario: a mast at a facing switch has one route for each leg
    When the routes are found
    Then "830NAB" has routes aligned "829 NORMAL, 827 NORMAL; 829 REVERSE"
    And "830SAB" has routes aligned "829 REVERSE"
    And "828SA" has routes aligned "827 NORMAL, 829 NORMAL; 827 REVERSE, 827D REVERSE"
    And "828NA" has routes aligned "827D REVERSE, 827 REVERSE"

  Scenario: an automatic mast displays no route
    When the routes are found
    Then "832SA" has no routes
    And "832NA" has no routes

  Scenario: a route states its entering demand, its circuits, its entrance and its approach
    When the routes are found
    Then the route of "830SAB" aligned "829 REVERSE" is demanded by "830(RIGHT)"
    And the route of "830SAB" aligned "829 REVERSE" passes "829T1, 832T"
    And the route of "830SAB" aligned "829 REVERSE" enters at "829T1"
    And the route of "830SAB" aligned "829 REVERSE" approaches over "1NAT"

  Scenario: the next automatic mast ends the route and is named with no demand
    When the routes are found
    Then the route of "830SAB" aligned "829 REVERSE" ends at mast "832SA" with no demand

  Scenario: a neighbour's mast ends the route, named and demanded in its own interlocking
    When the routes are found
    Then the route of "830NAB" aligned "829 NORMAL, 827 NORMAL" ends at mast "Y:816NAB" demanding "Y:816(LEFT)"
    And the route of "830NAB" aligned "829 NORMAL, 827 NORMAL" passes "829T1, 827T1, 2NAT"

  Scenario: an opposing mast is passed and stated as an opposing demand
    When the routes are found
    Then the route of "830NAB" aligned "829 NORMAL, 827 NORMAL" is opposed by masts "828SA"
    And the route of "830NAB" aligned "829 NORMAL, 827 NORMAL" is opposed by demands "828(RIGHT)"
    And the route of "830SAB" aligned "829 REVERSE" is opposed by masts "830NAB, 832NA"
    And the route of "830SAB" aligned "829 REVERSE" is opposed by demands "830(LEFT)"

  Scenario: a converging movement is a different route, not an opposing term
    When the routes are found
    Then the route of "828SA" aligned "827 NORMAL, 829 NORMAL" is opposed by masts "830NAB, 832NA"

  Scenario: a route to a NextCP ends at the limit
    When the routes are found
    Then the route of "830NAB" aligned "829 REVERSE" ends at the limit "NEXT_CP"
    And the route of "830NAB" aligned "829 REVERSE" passes "829T1, 1NAT"
    And the route of "830NAB" aligned "829 REVERSE" is opposed by masts "830SAB"

  Scenario: a route passes a regime marker and continues to the end of track
    When the routes are found
    Then the route of "828SA" aligned "827 REVERSE, 827D REVERSE" ends at the limit "BUMPER"
    And the route of "828SA" aligned "827 REVERSE, 827D REVERSE" passes "827T1, 01T"
    And the route of "828SA" aligned "827 REVERSE, 827D REVERSE" passes regimes "GCOR_RULE_10, GCOR_RULE_10"

  Scenario: a route from yard limits passes the regime marker into CTC and continues to the end of track
    Gilroy Caltrain: the station tracks are under GCOR 6.13 (Yard Limits); the switch beyond the marker is under
    GCOR 10.0 (Rules Applicable Only in CTC).
    Given interlocking "U" has these appliances:
      | Name  | Appliance     | Style   | Kind       | TC  | CP Name | signal | heads | relations.facing |
      | 9     | switch        | powered |            | 9T1 | U       |        |       |                  |
      | 774NC | mast          |         | CONTROLLED |     | U       | 774    | C     | LEFT             |
      | 3T    | track_circuit |         |            |     | U       |        |       |                  |
    And interlocking "U" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | M1 | IRJ_SIGNAL | U       | U:774NC        |
      | M2 | IRJ        |         |                |
    And interlocking "U" has these ends:
      | Id | Kind    |
      | G1 | NEXT_CP |
      | G2 | NEXT_CP |
    And interlocking "U" has these policies:
      | Id | Kind           |
      | Q1 | GCOR_RULE_6_13 |
      | Q2 | GCOR_RULE_10   |
    And interlocking "U" has these wires:
      | Wire | Pins                       |
      | a    | M1.governed 3T.TC M2.A Q1.track |
      | b    | M2.B 9.C Q2.track          |
      | c    | 9.N G1.track               |
      | d    | 9.R G2.track               |
    And the desk has these levers for interlocking "U":
      | Name | Style  |
      | 774  | signal |
    When the routes are found
    Then "774NC" has routes aligned "9 NORMAL; 9 REVERSE"
    And the route of "774NC" aligned "9 NORMAL" ends at the limit "NEXT_CP"
    And the route of "774NC" aligned "9 NORMAL" passes "3T, 9T1"
    And the route of "774NC" aligned "9 NORMAL" passes regimes "GCOR_RULE_6_13, GCOR_RULE_10"

  Scenario: a route through yard limits is held to RESTRICTING
    The owner, 2026-11-13: GCOR 6.13 (Yard Limits) contributes RESTRICTING everywhere in yard limits; the word is
    reference data (regimes.ceilings). GCOR 10.0 (Rules Applicable Only in CTC) contributes nothing.
    Given interlocking "U" has these appliances:
      | Name  | Appliance     | Style   | Kind       | TC  | CP Name | signal | heads | relations.facing |
      | 9     | switch        | powered |            | 9T1 | U       |        |       |                  |
      | 774SA | mast          |         | CONTROLLED |     | U       | 774    | A     | RIGHT            |
      | 3T    | track_circuit |         |            |     | U       |        |       |                  |
      | 1T    | track_circuit |         |            |     | U       |        |       |                  |
    And interlocking "U" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | M1 | IRJ_SIGNAL | U       | U:774SA        |
      | M2 | IRJ        |         |                |
    And interlocking "U" has these ends:
      | Id | Kind    |
      | G1 | BUMPER  |
      | G2 | NEXT_CP |
    And interlocking "U" has these policies:
      | Id | Kind           |
      | Q1 | GCOR_RULE_6_13 |
      | Q2 | GCOR_RULE_10   |
    And interlocking "U" has these wires:
      | Wire | Pins                        |
      | a    | M1.approach 1T.TC           |
      | b    | M1.governed 9.C Q2.track    |
      | c    | 9.N M2.B                    |
      | d    | M2.A 3T.TC Q1.track G1.EoT  |
      | e    | 9.R G2.track                |
    And the desk has these levers for interlocking "U":
      | Name | Style  |
      | 774  | signal |
    When the routes are found
    Then the route of "774SA" aligned "9 NORMAL" ends at the limit "BUMPER"
    And the route of "774SA" aligned "9 NORMAL" passes regimes "GCOR_RULE_10, GCOR_RULE_6_13"
    And the route of "774SA" aligned "9 NORMAL" has ceiling "RESTRICTING"
    And the route of "774SA" aligned "9 REVERSE" has ceiling "CLEAR"

  Scenario: a route through a dependent derail takes the derail's stated ceiling for REVERSE
    When the routes are found
    Then the route of "828SA" aligned "827 REVERSE, 827D REVERSE" has ceiling "RESTRICTING"
    And the route of "828NA" aligned "827D REVERSE, 827 REVERSE" has ceiling "RESTRICTING"

  Scenario: a route that passes no stated ceiling is CLEAR, stated
    The owner, 2026-11-13: each term contributes one indication from its own value set; CLEAR is the unrestricted
    contribution. The ADR 0012 §5.4 heuristics join as contributions when the policies reference rows exist.
    When the routes are found
    Then the route of "830SAB" aligned "829 REVERSE" has ceiling "CLEAR"
    And the route of "830NAB" aligned "829 NORMAL, 827 NORMAL" has ceiling "CLEAR"

  Scenario: a controlled mast no lever works displays routes with no entering demand
    Given interlocking "X" has these appliances:
      | Name   | Appliance | Style  | Kind       | CP Name | signal | heads | relations.facing |
      | 830SAB | mast      | double | CONTROLLED | X       | 831    | A,B   | RIGHT            |
    When the routes are found
    Then the route of "830SAB" aligned "829 REVERSE" has no entering demand

  Scenario: on a reversing loop a route of a LEFT lever ends at a RIGHT signal
    Given interlocking "W" has these appliances:
      | Name | Appliance     | Kind       | CP Name | signal | heads | relations.facing |
      | 2NA  | mast          | CONTROLLED | W       | 2      | A     | LEFT             |
      | 4SA  | mast          | CONTROLLED | W       | 4      | A     | RIGHT            |
      | 3T   | track_circuit |            | W       |        |       |                  |
      | 5T   | track_circuit |            | W       |        |       |                  |
      | 7T   | track_circuit |            | W       |        |       |                  |
    And interlocking "W" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | K2 | IRJ_SIGNAL | W       | W:2NA          |
      | K4 | IRJ_SIGNAL | W       | W:4SA          |
    And interlocking "W" has these wires:
      | Wire | Pins                  |
      | a    | K2.approach 5T.TC     |
      | b    | K2.governed 3T.TC K4.approach |
      | c    | K4.governed 7T.TC     |
    And the desk has these levers for interlocking "W":
      | Name | Style  |
      | 2    | signal |
      | 4    | signal |
    When the routes are found
    Then the route of "2NA" aligned "nothing" ends at mast "4SA" demanding "4(RIGHT)"
    And the route of "2NA" aligned "nothing" passes "3T"

  @route.end
  Scenario: track that ends with nothing stated leaves the route without an end
    Given interlocking "W" has these appliances:
      | Name | Appliance     | Kind       | CP Name | signal | heads | relations.facing |
      | 2NA  | mast          | CONTROLLED | W       | 2      | A     | LEFT             |
      | 3T   | track_circuit |            | W       |        |       |                  |
    And interlocking "W" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | K2 | IRJ_SIGNAL | W       | W:2NA          |
    And interlocking "W" has these wires:
      | Wire | Pins              |
      | a    | K2.governed 3T.TC |
    When the routes are found
    Then it is reported as missing on "2NA"
    And the route of "2NA" aligned "nothing" has no end

  @route.entering
  Scenario: a facing switch toward a limit with no entering signal
    Given interlocking "V" has these appliances:
      | Name  | Appliance     | Style   | Kind       | TC    | CP Name | signal | heads | relations.facing |
      | 837   | switch        | powered |            | 837T1 | V       |        |       |                  |
      | 838NA | mast          |         | CONTROLLED |       | V       | 838    | A     | LEFT             |
      | 840NA | mast          |         | CONTROLLED |       | V       | 840    | A     | LEFT             |
    And interlocking "V" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | L1 | IRJ_SIGNAL | V       | V:838NA        |
      | L2 | IRJ_SIGNAL | V       | V:840NA        |
    And interlocking "V" has these ends:
      | Id | Kind    |
      | F1 | NEXT_CP |
    And interlocking "V" has these wires:
      | Wire | Pins                 |
      | a    | 837.C F1.track       |
      | b    | 837.N L1.governed    |
      | c    | 837.R L2.governed    |
    And the desk has these levers for interlocking "V":
      | Name | Style  |
      | 838  | signal |
      | 840  | signal |
    When the routes are found
    Then it is reported as missing on "837"
    And the route of "838NA" aligned "837 NORMAL" ends at the limit "NEXT_CP"

  @route.entering
  Scenario: a facing switch on yard-limits track expects no entering signal
    The owner, 2026-11-13: only track under signal indication (GCOR 10.0, Rules Applicable Only in CTC) expects a
    signal to enter a facing switch; a movement into yard limits (GCOR 6.13, Yard Limits) is made at restricted speed.
    Given interlocking "V" has these appliances:
      | Name  | Appliance     | Style   | Kind       | TC    | CP Name | signal | heads | relations.facing |
      | 837   | switch        | powered |            | 837T1 | V       |        |       |                  |
      | 838NA | mast          |         | CONTROLLED |       | V       | 838    | A     | LEFT             |
      | 840NA | mast          |         | CONTROLLED |       | V       | 840    | A     | LEFT             |
    And interlocking "V" has these joints:
      | Id | Kind       | CP Name | relations.mast |
      | L1 | IRJ_SIGNAL | V       | V:838NA        |
      | L2 | IRJ_SIGNAL | V       | V:840NA        |
    And interlocking "V" has these ends:
      | Id | Kind    |
      | F1 | NEXT_CP |
    And interlocking "V" has these policies:
      | Id | Kind           |
      | Q1 | GCOR_RULE_6_13 |
    And interlocking "V" has these wires:
      | Wire | Pins                       |
      | a    | 837.C F1.track Q1.track    |
      | b    | 837.N L1.governed          |
      | c    | 837.R L2.governed          |
    And the desk has these levers for interlocking "V":
      | Name | Style  |
      | 838  | signal |
      | 840  | signal |
    When the routes are found
    Then it is not reported
