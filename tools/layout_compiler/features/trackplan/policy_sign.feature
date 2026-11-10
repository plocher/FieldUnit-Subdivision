Feature: A policy sign, as drawn
  A sign's Kind and Direction are fields of its symbol, written as given. Its one pin To is the
  track side: on a track net it states the pins there. A regime marker (a GCOR Rule symbol) and
  the current-of-traffic sign are read alike; what a marker's extent is belongs to the model
  rules. (ADR 0013 §7.1, §8)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                        | Role      | Kind           | Direction | Appliance     | Name | CP Name |
      | H1  | Railroad-Trackplan:House                      | STRUCTURE | CONTROL_POINT  |           |               |      | East    |
      | TC1 | Railroad-Trackplan:Track Circuit              | APPLIANCE |                |           | track_circuit | 1NAT |         |
      | R1  | Railroad-Trackplan:GCOR Rule 9.14 DoT_Right   | POLICY    | GCOR_RULE_9_14 | RIGHT     |               |      |         |
      | R2  | Railroad-Trackplan:GCOR Rule 6.13 Yard Limits | POLICY    | GCOR_RULE_6_13 |           |               |      |         |

  Scenario: a sign's pin on the track
    Given these nets:
      | Net | Pins                |
      | t   | TC1.TC R1.To R2.To  |
    When the drawing is imported
    Then the row "R1" is written with Kind "GCOR_RULE_9_14"
    And the row "R1" is written with Direction "RIGHT"
    And the row "R2" is written with Kind "GCOR_RULE_6_13"
    And the row "R1" names "X:1NAT.TC" on side track
    And the row "R2" names "X:1NAT.TC" on side track

  Scenario: a sign on no net states no track
    Given these nets:
      | Net | Pins         |
      | t   | TC1.TC R2.To |
    When the drawing is imported
    Then the row "R1" states no relation track
