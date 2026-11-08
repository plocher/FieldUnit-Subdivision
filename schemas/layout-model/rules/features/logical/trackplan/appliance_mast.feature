Feature: What a mast is
  A mast states its Kind: CONTROLLED (the dispatcher controls it; it belongs in a control point),
  ABSOLUTE (automatic and absolute, an APB head block) or PERMISSIVE (automatic and permissive,
  with a number plate). A mast with none is missing; nothing is inferred from a CP Name or a plate.
  An automatic mast belongs to no control point and states no CP Name. A grade or restricting
  plate is a policy on the mast's signal wire and requires a PERMISSIVE mast. An automatic mast
  whose route passes a powered switch or derail is reported; the check sets nothing. An automatic
  mast is numbered for its signal location, like any mast. (ADR 0013 §5, §9)

  Background: two automatic masts back to back at signal location 832, under house East
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name  | Appliance     | Style  | Kind       |
      | 832T  | track_circuit |        |            |
      | 834T  | track_circuit |        |            |
      | 832NA | mast          | single | PERMISSIVE |
      | 832SA | mast          | single | PERMISSIVE |
    And interlocking "X" has these joints:
      | Id | Kind        | relations.masts     |
      | J1 | IRJ_SIGNALS | A=X:832NA B=X:832SA |
    And interlocking "X" has these wires:
      | Wire | Pins         |
      | a    | J1.A 832T.TC |
      | b    | J1.B 834T.TC |

  @mast.kind
  Scenario: a mast states what it is
    When the layout is derived
    Then it is not reported

  @mast.kind
  Scenario: a mast with no Kind
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind |
      | 832SA | mast      | single |      |
    When the layout is derived
    Then it is reported as missing on "832SA"

  @mast.kind
  Scenario: a mast with a Kind that is none of the three
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind      |
      | 832SA | mast      | single | AUTOMATIC |
    When the layout is derived
    Then it is reported as missing on "832SA"

  Scenario: an automatic mast belongs to no control point, a controlled one to its house
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 832NA | mast      | single | CONTROLLED |
    When the layout is derived
    Then "832NA" belongs to control point "X:East"
    And "832SA" belongs to no control point

  @mast.control_point
  Scenario: an automatic mast that states a CP Name
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind       | CP Name |
      | 832SA | mast      | single | PERMISSIVE | East    |
    When the layout is derived
    Then it is reported as a warning on "832SA"
    And "832SA" belongs to no control point

  @mast.powered
  Scenario: an automatic mast whose route passes a powered switch
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 9    | switch    | powered |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | b    | J1.B 834T.TC 9.C |
    When the layout is derived
    Then it is reported as a warning on "832SA"

  @mast.powered
  Scenario Outline: a switch that is not powered may lie in an automatic mast's route
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | CP Name |
      | 9    | switch    | <style> | East    |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | b    | J1.B 834T.TC 9.C |
    When the layout is derived
    Then it is not reported

    Examples: hand-throw, sensed hand-throw, spring and electrically locked hand-throw
      | style         |
      | manual        |
      | manual_sensed |
      | spring        |
      | lock          |

  @plate.mast
  Scenario: a plate on a permissive mast
    Given interlocking "X" has these policies:
      | Id  | Kind       | relations.mast |
      | PL1 | RULE_290_G | X:832SA        |
    When the layout is derived
    Then it is not reported

  @plate.mast
  Scenario: a plate on no mast's signal wire
    Given interlocking "X" has these policies:
      | Id  | Kind       |
      | PL1 | RULE_290_R |
    When the layout is derived
    Then it is reported as an error on "PL1"

  @plate.mast
  Scenario: a plate on a controlled mast
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 832SA | mast      | single | CONTROLLED |
    And interlocking "X" has these policies:
      | Id  | Kind       | relations.mast |
      | PL1 | RULE_290_G | X:832SA        |
    When the layout is derived
    Then it is reported as an error on "PL1"

  @mast.grammar
  Scenario: an automatic mast is numbered for its signal location
    When the layout is derived
    Then it is not reported

  @mast.grammar
  Scenario: a mast whose name is not a signal number and its head letters
    Given interlocking "X" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | EastA | mast      | single | PERMISSIVE |
    And interlocking "X" has these joints:
      | Id | Kind        | relations.masts     |
      | J1 | IRJ_SIGNALS | A=X:832NA B=X:EastA |
    When the layout is derived
    Then it is reported as information on "EastA"
