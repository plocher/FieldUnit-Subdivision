Feature: The aspect name a JMRI signal mast driver sends for an indication
  A translation table is reference data, keyed by signal system, indication and mast Kind, and gives JMRI's "aspect name".
  The tables are ours and editable. JMRI's appearance files are a source for names, not an authority.
  Kind is in the key because some systems fold the plate into the name: STOP on a controlled or absolute mast is not the same name as on a permissive one.
  An indication with no row is not presentable in that system.

  Scenario Outline: the basic system
    Given the signal system "basic"
    Then the indication "<indication>" on a <kind> mast has the aspect name "<name>"

    Examples:
      | indication         | kind       | name               |
      | CLEAR              | CONTROLLED | Clear              |
      | APPROACH           | CONTROLLED | Approach           |
      | STOP               | CONTROLLED | Stop               |
      | STOP               | PERMISSIVE | Stop               |
      | DIVERGING_CLEAR    | CONTROLLED | Diverging Clear    |
      | DIVERGING_APPROACH | CONTROLLED | Diverging Approach |
      | RESTRICTING        | CONTROLLED | Restricting        |

  Scenario Outline: the Southern Pacific system of 1969
    Given the signal system "SPTCO-1969"
    Then the indication "<indication>" on a <kind> mast has the aspect name "<name>"

    Examples:
      | indication           | kind       | name                                    |
      | CLEAR                | CONTROLLED | Block Signal Green                      |
      | APPROACH             | CONTROLLED | Approach Signal Yellow                  |
      | RESTRICTING          | CONTROLLED | Restricting                             |
      | STOP                 | CONTROLLED | Home Signal Red                         |
      | STOP                 | ABSOLUTE   | Home Signal Red                         |
      | STOP                 | PERMISSIVE | Stop and Proceed                        |
      | DIVERGING_CLEAR      | CONTROLLED | Block Signal Green for Diverging Route  |
      | APPROACH_DIVERGING   | CONTROLLED | Block Signal Yellow over Green          |
      | APPROACH_MEDIUM      | CONTROLLED | Approach Medium - Flashing Yellow       |
      | DIVERGING_APPROACH   | CONTROLLED | Home Signal Yellow for Diverging Route  |
      | DIVERGING_RESTRICTING | CONTROLLED | Home Signal Red over Lunar             |

  Scenario Outline: a word the system does not present
    Given the signal system "<system>"
    Then the indication "<indication>" on a <kind> mast has no aspect name

    Examples:
      | system     | indication       | kind       |
      | basic      | APPROACH_MEDIUM  | CONTROLLED |
      | SPTCO-1969 | ADVANCE_APPROACH | CONTROLLED |

  Scenario: a system no table names
    Given the signal system "SP-1890"
    Then the indication "STOP" on a CONTROLLED mast has no aspect name

  Scenario: the user's own table layers over the shipped one
    Given the signal system "SPTCO-1969"
    And the user's table says "DIVERGING_RESTRICTING" on a CONTROLLED mast is "Home Signal Red over Yellow"
    Then the indication "DIVERGING_RESTRICTING" on a CONTROLLED mast has the aspect name "Home Signal Red over Yellow"
    And the indication "STOP" on a CONTROLLED mast has the aspect name "Home Signal Red"
