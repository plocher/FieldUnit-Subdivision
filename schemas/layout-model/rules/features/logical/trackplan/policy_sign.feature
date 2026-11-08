Feature: A sign states its rule for the track it stands on
  A policy sign states its Kind and Direction as given and the track it stands on. Under
  RULE_251 the sign's LEFT or RIGHT is the current of traffic: the lever direction of the
  signals that govern with it. A RULE_251 sign inside interlocking limits states the current
  of traffic on that track and nothing more. RULE_261, RULE_105 and RULE_93 signs state BOTH,
  which adds nothing to their Kind. That the signs of one block agree with each other and with
  its masts is the blocks library's. (ADR 0013 §8)

  Background:
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name | Appliance     |
      | 1NAT | track_circuit |

  @policy.direction
  Scenario: a RULE_251 sign states the current of traffic on its track
    Given interlocking "X" has these policies:
      | Id | Kind     | Direction |
      | R1 | RULE_251 | RIGHT     |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | t    | R1.track 1NAT.TC |
    When the layout is derived
    Then sign "R1" stands on circuit "X:1NAT"
    And it is not reported

  @policy.direction
  Scenario: a RULE_251 sign whose direction is not a current of traffic
    Given interlocking "X" has these policies:
      | Id | Kind     | Direction |
      | R1 | RULE_251 | BOTH      |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | t    | R1.track 1NAT.TC |
    When the layout is derived
    Then it is reported as missing on "R1"

  @policy.direction
  Scenario: a RULE_261 sign states both directions and nothing more
    Given interlocking "X" has these policies:
      | Id | Kind     | Direction |
      | R1 | RULE_261 | BOTH      |
    And interlocking "X" has these wires:
      | Wire | Pins             |
      | t    | R1.track 1NAT.TC |
    When the layout is derived
    Then sign "R1" stands on circuit "X:1NAT"
    And it is not reported

  @policy.track
  Scenario: a sign on no track
    Given interlocking "X" has these policies:
      | Id | Kind     | Direction |
      | R1 | RULE_251 | RIGHT     |
    When the layout is derived
    Then it is reported as missing on "R1"
