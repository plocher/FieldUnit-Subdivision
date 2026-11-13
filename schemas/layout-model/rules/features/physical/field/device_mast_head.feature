Feature: A head is a position on its mast
  A mast states its atoms: its signal number, the way it faces, and the letters of its heads, top down.
  The Name is a label composed of them; nothing reads the Name. (ADR 0003 rules 5 to 7, the owner 2026-11-12)
  A field mast device has the Name of its trackplan mast and one pin for each head position: A, B, C, top down.
  The k-th head letter is the k-th pin: on 784WBC, pin A is head B and pin B is head C.
  A head has no name. It is the position its IND is wired to, and its Style is its model.
  A position presents the head words of its head's model table; any number of heads may share a position.
  A train order board's face follows the same shape: keyed by the pin, never by a letter.
  The words a mast must show are within what its positions present. Until the demand is derived (#62), a mast
  states its demand as an explicit Indications list, the settled exception; a mast with several positions is matched
  through the policy table, which is not seeded yet.

  Scenario: 784WBC has heads B and C by name; pin A is head B and pin B is head C
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads | relations.facing |
      | 784WBC | mast      | double | CONTROLLED | 784    | B,C   | LEFT             |
    And field mast "784WBC" has these heads:
      | Position | Style |
      | A        | TypeD |
      | B        | TypeD |
    When the layout is derived
    Then "784WBC" has head positions "A, B"
    And position "A" of "784WBC" is head "B"
    And position "B" of "784WBC" is head "C"
    And the head on position "A" of "784WBC" is head "B"

  Scenario: a single-position mast: 774NC is signal 774's head C on pin A
    Given interlocking "Gilroy Caltrain" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads | relations.facing |
      | 774NC | mast      | single | CONTROLLED | 774    | C     | LEFT             |
    And field mast "774NC" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then "774NC" has head positions "A"
    And position "A" of "774NC" is head "C"

  Scenario: a mast's positions are its letters, with a head wired or not
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads |
      | 784EAB | mast      | double | CONTROLLED | 784    | A,B   |
    And field mast "784EAB" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then "784EAB" has head positions "A, B"
    And position "B" of "784EAB" is head "B"
    And position "B" of "784EAB" presents nothing yet

  Scenario: a position presents the words of its head model
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then position "A" of "784EA" presents "STOP, APPROACH, ADVANCE_APPROACH, CLEAR, DARK"

  @head.model
  Scenario: a head whose Style names no head model row
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | CPL   |
    When the layout is derived
    Then it is reported as missing on "1"

  @mast.device
  Scenario: a mast with no field mast device
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
    When the layout is derived
    Then it is reported as missing on "784EA"

  @mast.device
  Scenario: a field mast device with no head wired
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
    And field mast device "784EA" exists
    When the layout is derived
    Then it is reported as missing on "784EA"

  @mast.presents
  Scenario: a mast whose head cannot present a word the mast must show
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads | Indications           |
      | 784EA | mast      | single | CONTROLLED | 784    | A     | STOP, APPROACH, CLEAR |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | LQ2   |
    When the layout is derived
    Then "784EA" must show "STOP, APPROACH, CLEAR"
    And it is reported as information on "784EA"

  @mast.presents
  Scenario: a mast whose head presents every word it must show
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads | Indications           |
      | 784EA | mast      | single | CONTROLLED | 784    | A     | STOP, APPROACH, CLEAR |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
    When the layout is derived
    Then it is not reported

  @head.position
  Scenario: two heads on one mast pin with different indication sets are reported as information
    Given interlocking "Luchessa" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
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
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 784EA | mast      | single | CONTROLLED | 784    | A     |
    And field mast "784EA" has these heads:
      | Position | Style |
      | A        | TypeD |
      | A        | TypeD |
    When the layout is derived
    Then it is not reported

  @mast.heads
  Scenario: a head wired to a position the mast's heads do not letter
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads |
      | 784EAB | mast      | double | CONTROLLED | 784    | A,B   |
    And field mast "784EAB" has these heads:
      | Position | Style |
      | A        | TypeD |
      | C        | TypeD |
    When the layout is derived
    Then it is reported as an error on "784EAB"

  @mast.letters
  Scenario: one head letter on two masts of one signal
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads | relations.facing |
      | 784EAB | mast      | double | CONTROLLED | 784    | A,B   | RIGHT            |
      | 784EB  | mast      | single | CONTROLLED | 784    | B     | RIGHT            |
    When the layout is derived
    Then it is reported as an error on "784EB"

  @mast.letters
  Scenario: the two sides of a signal each have their own letters
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads | relations.facing |
      | 784EAB | mast      | double | CONTROLLED | 784    | A,B   | RIGHT            |
      | 784WBC | mast      | double | CONTROLLED | 784    | B,C   | LEFT             |
    When the layout is derived
    Then it is not reported
