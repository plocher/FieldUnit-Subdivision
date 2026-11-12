Feature: A head is a position on its mast
  A field mast device has the Name of its trackplan mast and one pin for each head position: A, B, C, top down.
  A head has no name. It is the position its IND is wired to, and its Style is its model.
  A position presents the head words of its head's model table; any number of heads may share a position.
  The words a mast must show are within what its positions present. Until the demand is derived (#62), a mast
  states its demand as an explicit Indications list, the settled exception; a mast with several positions is matched
  through the policy table, which is not seeded yet.

  Scenario: two heads on a double mast
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       |
      | 784EAB | mast      | double | CONTROLLED |
    And field mast "784EAB" has these heads:
      | Position | Style |
      | A        | TypeD |
      | B        | SA    |
    When the layout is derived
    Then "784EAB" has head positions "A, B"

  Scenario: a position presents the words of its head model
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then position "A" of "784EA" presents "STOP, APPROACH, ADVANCE_APPROACH, CLEAR, DARK"

  @head.model
  Scenario: a head whose Style names no head model row
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | CPL   |
    When the layout is derived
    Then it is reported as missing on "1"

  @mast.device
  Scenario: a mast with no field mast device
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    When the layout is derived
    Then it is reported as missing on "784EA"

  @mast.device
  Scenario: a field mast device with no head wired
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    And field mast device "784EA" exists
    When the layout is derived
    Then it is reported as missing on "784EA"

  @mast.presents
  Scenario: a mast whose head cannot present a word the mast must show
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | Indications           |
      | 784EA | mast      | single | CONTROLLED | STOP, APPROACH, CLEAR |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | LQ2   |
    When the layout is derived
    Then "784EA" must show "STOP, APPROACH, CLEAR"
    And it is reported as information on "784EA"

  @mast.presents
  Scenario: a mast whose head presents every word it must show
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | Indications           |
      | 784EA | mast      | single | CONTROLLED | STOP, APPROACH, CLEAR |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then it is not reported

  @head.position
  Scenario: two heads on one mast pin with different indication sets are reported as information
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
      | A        | LQ2   |
    When the layout is derived
    Then position "A" of "784EA" presents "STOP, APPROACH, ADVANCE_APPROACH, CLEAR, DARK"
    And it is reported as information on "784EA"

  @head.position
  Scenario: two heads on one mast pin with the same indication set
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
      | A        | TypeD |
    When the layout is derived
    Then it is not reported

  @mast.heads
  Scenario: a head wired to a position the mast's name does not letter
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       |
      | 784EAB | mast      | double | CONTROLLED |
    And field mast "784EAB" has these heads:
      | Position | Style |
      | A        | TypeD |
      | C        | TypeD |
    When the layout is derived
    Then it is reported as an error on "784EAB"
