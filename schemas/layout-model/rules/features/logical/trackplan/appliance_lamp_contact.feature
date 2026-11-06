Feature: Where a lamp or contact is
  A lamp or contact appliance can state the track circuit it is at.
  That circuit is a circuit of the appliance's own interlocking.
  A lamp or contact that states no circuit is placed by its Milepost and CP Name.

  @pending
  Scenario: a contact at a track circuit of its interlocking
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance     | relations.circuit |
      | 1NAT | track_circuit |                   |
      | HTR  | contact       | Luchessa:1NAT     |
    When the layout is derived
    Then "HTR" is on circuit "Luchessa:1NAT"

  @pending @appliance.circuit
  Scenario: a contact at a track circuit of another interlocking
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | relations.circuit |
      | HTR  | contact   | Sargent:2NAT      |
    And interlocking "Sargent" has these appliances:
      | Name | Appliance     |
      | 2NAT | track_circuit |
    When the layout is derived
    Then it is reported as an error on "HTR"

  @pending @appliance.circuit
  Scenario: a lamp that states no circuit
    Given interlocking "Luchessa" has house "Luchessa"
    And interlocking "Luchessa" has these appliances:
      | Name | Appliance | Milepost | CP Name  |
      | NFL  | lamp      | 78.1     | Luchessa |
    When the layout is derived
    Then it is not reported
