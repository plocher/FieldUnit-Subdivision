Feature: A head is a position on its mast
  A field mast device has the Name of its trackplan mast and one pin for each head position: A, B, C, top down.
  A head has no name. It is the position its IND is wired to.
  A position presents the head words of its head's model table.
  The words a mast must show are within what its positions present through the policy table.

  @pending
  Scenario: two heads on a double mast
    Given field mast "784EAB" has these heads:
      | Position | Style |
      | A        | TypeD |
      | B        | SA    |
    When the layout is derived
    Then "784EAB" has head positions "A, B"

  @pending
  Scenario: a position presents the words of its head model
    Given field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then position "A" of "784EA" presents "STOP, APPROACH, ADVANCE_APPROACH, CLEAR, DARK"

  @pending @mast.device
  Scenario: a mast with no field mast device
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       |
      | 784EA | mast      | single | CONTROLLED |
    When the layout is derived
    Then it is reported as missing on "784EA"

  @pending @mast.presents
  Scenario: a mast whose head cannot present a word the mast must show
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | Indications           |
      | 784EA | mast      | single | CONTROLLED | STOP, APPROACH, CLEAR |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | LQ    |
    When the layout is derived
    Then it is reported as an error on "784EA"
