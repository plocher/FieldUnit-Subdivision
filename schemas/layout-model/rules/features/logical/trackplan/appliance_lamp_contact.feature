Feature: Where a lamp, contact or actuator is
  A lamp, contact or actuator appliance can state the track circuit it is at: its circuit relation.
  That circuit is a circuit of the appliance's own interlocking: a track circuit marker or a switch's
  OS circuit (its TC) of that interlocking.
  One that states no circuit is placed by its Milepost and CP Name.
  Lamp, contact and actuator are read the same way; no rule tells an actuator from a lamp yet.

  Scenario: a contact at a track circuit of its interlocking
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance     | relations.circuit |
      | 1NAT | track_circuit |                   |
      | HTR  | contact       | Luchessa:1NAT     |
    When the layout is derived
    Then "HTR" is on circuit "Luchessa:1NAT"

  Scenario: an actuator at a switch's OS circuit
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | TC    | relations.circuit |
      | 783  | switch    | 783T1 |                   |
      | HTR  | actuator  |       | Luchessa:783T1    |
    When the layout is derived
    Then "HTR" is on circuit "Luchessa:783T1"

  @appliance.circuit
  Scenario: a contact at a track circuit of another interlocking
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | relations.circuit |
      | HTR  | contact   | Sargent:2NAT      |
    And interlocking "Sargent" has these appliances:
      | Name | Appliance     |
      | 2NAT | track_circuit |
    When the layout is derived
    Then it is reported as an error on "HTR"

  @appliance.circuit
  Scenario: a lamp at a circuit its interlocking does not have
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | relations.circuit |
      | NFL  | lamp      | Luchessa:9NAT     |
    When the layout is derived
    Then it is reported as an error on "NFL"

  @appliance.circuit
  Scenario: a lamp that states no circuit
    Given interlocking "Luchessa" has house "Luchessa"
    And interlocking "Luchessa" has these appliances:
      | Name | Appliance | Milepost | CP Name  |
      | NFL  | lamp      | 78.1     | Luchessa |
    When the layout is derived
    Then it is not reported
