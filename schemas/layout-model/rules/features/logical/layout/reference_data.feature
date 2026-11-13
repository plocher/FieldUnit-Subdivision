Feature: Reference data is selected by the layout and resolved per entity
  The reference tables are data files under the schema folder, the source and not an output (ADR 0012 §6; the owner, 2026-11-13).
  The layout selects: its Railroad, Era and Rulebook, stated on the Railroad symbol, choose the row of every layout-keyed table.
  The selection is stated, never copied; derived.reference on the layout names the row each table resolved to.
  An entity's own fields choose the rest: a head's Style, a driver's JMRI.SignalSystem, a code line's Kind.
  The user's own tables layer over the shipped ones; the user's wins. A key with no row resolves to nothing, never a guess.
  A consumer reads the resolved words from the file and never a table by name.

  Scenario: the layout's rulebook has no row of its own and takes the default
    Given the layout states Railroad "Southern Pacific", Era "1960+" and Rulebook "GCOR"
    When the layout is derived
    Then the layout resolved "trainOrderInputs" to row "default"
    And the layout resolved no row of "policies"

  Scenario: a rulebook with rows of its own resolves to them
    Given the user's train order inputs for rulebook "SP" rank "STOP=STOP, SLOW=RESTRICTING" and rest "CLEAR"
    And the user's policy for rulebook "SP" with 2 heads says "CLEAR = CLEAR, STOP; STOP = STOP, STOP"
    And the layout states Rulebook "SP"
    When the layout is derived
    Then the layout resolved "trainOrderInputs" to row "SP"
    And the layout resolved "policies" to row "SP"

  Scenario: a layout that states no rulebook takes the default
    When the layout is derived
    Then the layout resolved "trainOrderInputs" to row "default"

  Scenario: a US&S 506 code line addresses each house and carries the default token forms
    Given the layout has code line "Line" of Kind "USS506"
    When the layout is derived
    Then code line "Line" has station "house"
    And code line "Line" has templates "switch: {name}NWK, {name}RWK"
    And code line "Line" has templates "lock: {name}WLK, {name}WLQK"
    And code line "Line" has templates "signal: {lever}NGK, {lever}SGK, {lever}TEK"

  Scenario: an AAR token line addresses the interlocking as one station
    Given the layout has code line "Line" of Kind "AAR"
    When the layout is derived
    Then code line "Line" has station "interlocking"
    And code line "Line" has templates "track_circuit: {name}K"

  Scenario: the user's token table layers over the shipped one, per class
    Given the layout has code line "Line" of Kind "AAR"
    And the user's indication tokens for encoding "AAR" class "lock" are "{name}LK"
    When the layout is derived
    Then code line "Line" has templates "lock: {name}LK"
    And code line "Line" has templates "switch: {name}NWK, {name}RWK"
