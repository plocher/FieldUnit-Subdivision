Feature: The indication ceiling of a switch
  The route derivation sets the ceiling of each route.
  IndicationCeiling on a switch or derail is empty by default.
  Filled, it is an override of two indication words, NORMAL/REVERSE.
  A route through the appliance in that position can never show better than the word.

  @pending
  Scenario: a switch that states no ceiling
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | Style   | IndicationCeiling |
      | 783  | switch    | powered |                   |
    When the layout is derived
    Then a route through "783" NORMAL takes the ceiling the route derivation sets
    And a route through "783" REVERSE takes the ceiling the route derivation sets

  @pending
  Scenario: a switch that states a ceiling for each position
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | Style   | IndicationCeiling    |
      | 783  | switch    | powered | APPROACH/RESTRICTING |
    When the layout is derived
    Then a route through "783" NORMAL shows no better than "APPROACH"
    And a route through "783" REVERSE shows no better than "RESTRICTING"

  @pending
  Scenario: a derail is derailing in its normal position
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | Style  | IndicationCeiling |
      | 795D | switch    | derail,powered | STOP/RESTRICTING |
    When the layout is derived
    Then a route through "795D" NORMAL shows no better than "STOP"
    And a route through "795D" REVERSE shows no better than "RESTRICTING"

  @pending
  Scenario: a hand-operated switch that states no ceiling
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | Style  | IndicationCeiling |
      | 5    | switch    | manual |                   |
    When the layout is derived
    Then a route through "5" NORMAL takes the reference data's ceiling for a hand-operated switch
    And a route through "5" REVERSE takes the reference data's ceiling for a hand-operated switch

  @pending @ceiling.words
  Scenario Outline: a ceiling that is not two indication words
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | Style   | IndicationCeiling |
      | 783  | switch    | powered | <ceiling>         |
    When the layout is derived
    Then it is reported as an error on "783"

    Examples:
      | ceiling                |
      | RESTRICTING            |
      | STOP/RESTRICTING/CLEAR |
      | STOP/GREEN             |
