Feature: Block track between control points
  Block track is drawn from one control point to the next, across sheets where needed, and
  belongs to the layout, not to an interlocking. A track wire that joins two interlockings is
  block track when it is plain track: the other interlocking's marker names the circuit on
  this side, and no consumer and no token come of it. A dispatcher-controlled switch or derail
  (Style powered or dual) lies within a control point, never in block track; a hand-throw,
  spring, electrically locked hand-throw or local switch (a machine the crew works from a fascia
  lever, not the dispatcher's) may lie in a block whatever CP Name it states. Inside CTC the drawn
  block replaces the NextCP; a NextCP stays for a neighbour that is not drawn, and one marked
  off_layout says its neighbour never will be. (ADR 0013 §4, §7.1, §21 gap 7)

  Background: the home signal 836NAB of house East faces the block toward Y
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name   | Appliance     | Style  | Kind       |
      | 1SAT   | track_circuit |        |            |
      | 836NAB | mast          | double | CONTROLLED |
    And interlocking "X" has these joints:
      | Id | Kind       | relations.mast |
      | J1 | IRJ_SIGNAL | X:836NAB       |

  @reference.track
  Scenario: plain track drawn to the next interlocking's marker is block track
    Given interlocking "X" has these wires:
      | Wire | Pins                   |
      | g    | J1.governed 1SAT.TC    |
      | b    | J1.approach Y:836T.TC  |
    When the layout is derived
    Then joint "J1" governs over "X:1SAT" and approaches over "Y:836T"
    And it is not reported

  @reference.track
  Scenario Outline: a switch that is not dispatcher-controlled may lie in the block
    Given interlocking "Y" has these appliances:
      | Name | Appliance | Style   | CP Name |
      | 5    | switch    | <style> | West    |
    And interlocking "X" has these wires:
      | Wire | Pins                |
      | g    | J1.governed 1SAT.TC |
      | b    | J1.approach Y:5.R   |
    When the layout is derived
    Then it is not reported

    Examples: hand-throw, sensed hand-throw, spring, electrically locked hand-throw and local
      | style         |
      | manual        |
      | manual_sensed |
      | spring        |
      | lock          |
      | local         |

  @reference.track
  Scenario: a dispatcher-controlled switch on the wire that joins the interlockings
    Given interlocking "Y" has these appliances:
      | Name | Appliance | Style   |
      | 7    | switch    | powered |
    And interlocking "X" has these wires:
      | Wire | Pins                |
      | g    | J1.governed 1SAT.TC |
      | b    | J1.approach Y:7.R   |
    When the layout is derived
    Then it is reported as an error on "X"

  @reference.track
  Scenario: a switch the file does not have cannot be shown not dispatcher-controlled
    Given interlocking "X" has these wires:
      | Wire | Pins                |
      | g    | J1.governed 1SAT.TC |
      | b    | J1.approach Y:7.R   |
    When the layout is derived
    Then it is reported as an error on "X"

  @next_cp.drawn
  Scenario: a NextCP standing on track that is drawn through to its neighbour
    Given interlocking "X" has these ends:
      | Id  | Kind    | Interlocking |
      | NX1 | NEXT_CP | Y            |
    And interlocking "Y" has these ends:
      | Id  | Kind    | Interlocking |
      | NX2 | NEXT_CP | X            |
    And interlocking "X" has these wires:
      | Wire | Pins                            |
      | g    | J1.governed 1SAT.TC             |
      | b    | J1.approach NX1.track Y:836T.TC |
    When the layout is derived
    Then it is reported as a warning on "NX1"

  @next_cp.off_layout
  Scenario: a NextCP to an interlocking that is not in this file
    Given interlocking "X" has these ends:
      | Id  | Kind    | Interlocking |
      | NX1 | NEXT_CP | Hollister    |
    When the layout is derived
    Then it is reported as information on "X"

  @next_cp.off_layout
  Scenario: a NextCP marked off_layout says its neighbour will never be drawn
    Given interlocking "X" has these ends:
      | Id  | Kind    | Interlocking | Style      |
      | NX1 | NEXT_CP | Hollister    | off_layout |
    When the layout is derived
    Then it is not reported

  @next_cp.drawn_neighbour
  Scenario: a NextCP marked off_layout to an interlocking that is in this file
    Given interlocking "X" has these ends:
      | Id  | Kind    | Interlocking | Style      |
      | NX1 | NEXT_CP | Y            | off_layout |
    And interlocking "Y" has these ends:
      | Id  | Kind    | Interlocking |
      | NX2 | NEXT_CP | X            |
    When the layout is derived
    Then it is reported as a warning on "NX1"

  @next_cp.pair
  Scenario: a NextCP whose neighbour has none back
    Given interlocking "X" has these ends:
      | Id  | Kind    | Interlocking |
      | NX1 | NEXT_CP | Y            |
    And interlocking "Y" has these appliances:
      | Name | Appliance     |
      | 836T | track_circuit |
    When the layout is derived
    Then it is reported as an error on "X"

  @next_cp.interlocking
  Scenario: a NextCP that names no interlocking
    Given interlocking "X" has these ends:
      | Id  | Kind    |
      | NX1 | NEXT_CP |
    When the layout is derived
    Then it is reported as missing on "NX1"
