Feature: A policy sign, as drawn
  A sign's Kind and Direction are fields of its symbol, written as given. Its one pin, To or
  Track whatever the library calls it, is the track side: on a track net it states the pins
  there. (ADR 0013 §8)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                      | Role      | Kind          | Direction | Appliance     | Name | CP Name |
      | H1  | Railroad-Trackplan:House                    | STRUCTURE | CONTROL_POINT |           |               |      | East    |
      | TC1 | Railroad-Trackplan:Track Circuit            | APPLIANCE |               |           | track_circuit | 1NAT |         |
      | R1  | Railroad-Trackplan:Rule251-DoT-Right        | POLICY    | RULE_251      | RIGHT     |               |      |         |
      | R2  | Railroad-Trackplan:Rule261-DoT-BiDirectional | POLICY   | RULE_261      | BOTH      |               |      |         |

  Scenario: a sign's pin on the track
    Given these nets:
      | Net | Pins                   |
      | t   | TC1.TC R1.To R2.Track  |
    When the drawing is imported
    Then the row "R1" is written with Kind "RULE_251"
    And the row "R1" is written with Direction "RIGHT"
    And the row "R1" names "X:1NAT.TC" on side track
    And the row "R2" names "X:1NAT.TC" on side track

  Scenario: a sign on no net states no track
    Given these nets:
      | Net | Pins         |
      | t   | TC1.TC R2.Track |
    When the drawing is imported
    Then the row "R1" states no relation track
