Feature: A signal lever works the masts of its signal
  A desk signal lever is named for a signal number. It works every mast of its interlocking that states that
  signal number, whichever way each faces; the link is the stated number, never a reading of a mast's Name.
  A CONTROLLED mast is the dispatcher's: a desk signal lever of its signal number must be on a column of the
  office. One with none is missing, like a powered switch that no lever works. An ABSOLUTE or PERMISSIVE mast
  is automatic and has no lever. (ADR 0003 rule 5, ADR 0013 §5; the owner 2026-11-12)

  Background: Luchessa's signal 784, two masts
    Given interlocking "Luchessa" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads | relations.facing |
      | 784EAB | mast      | double | CONTROLLED | 784    | A,B   | RIGHT            |
      | 784WBC | mast      | double | CONTROLLED | 784    | B,C   | LEFT             |

  Scenario: the desk lever 784 works both masts of signal 784
    Given the desk has these levers for interlocking "Luchessa":
      | Name | Style  |
      | 784  | signal |
    When the layout is derived
    Then lever "784" serves "Luchessa:784"
    And lever "784" works masts "Luchessa:784EAB, Luchessa:784WBC"

  @lever.serves
  Scenario: a signal lever whose number no mast states
    Given the desk has these levers for interlocking "Luchessa":
      | Name | Style  |
      | 786  | signal |
    When the layout is derived
    Then it is reported as an error on "0"

  @mast.lever
  Scenario: a controlled mast with a desk lever
    Given the desk has these levers for interlocking "Luchessa":
      | Name | Style  |
      | 784  | signal |
    When the layout is derived
    Then it is not reported

  @mast.lever
  Scenario: Sargent's 836NAB, 836SA and 836SB are controlled but no desk lever 836 exists
    Given interlocking "Sargent" has these appliances:
      | Name   | Appliance | Style  | Kind       | signal | heads |
      | 836NAB | mast      | double | CONTROLLED | 836    | A,B   |
      | 836SA  | mast      | single | CONTROLLED | 836    | A     |
      | 836SB  | mast      | dwarf  | CONTROLLED | 836    | B     |
    And the desk has these levers for interlocking "Luchessa":
      | Name | Style  |
      | 784  | signal |
    When the layout is derived
    Then it is reported as missing on "836NAB"
    And it is reported as missing on "836SA"
    And it is reported as missing on "836SB"

  @mast.lever
  Scenario: an automatic mast has no lever
    Given interlocking "Sargent" has these appliances:
      | Name  | Appliance | Style  | Kind       | signal | heads |
      | 834NA | mast      | single | PERMISSIVE | 834    | A     |
      | 832SA | mast      | single | ABSOLUTE   | 832    | A     |
    And the desk has these levers for interlocking "Luchessa":
      | Name | Style  |
      | 784  | signal |
    When the layout is derived
    Then it is not reported
