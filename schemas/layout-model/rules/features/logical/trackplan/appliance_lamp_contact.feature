Feature: Where a lamp, contact or actuator is
  A lamp, contact or actuator appliance can state the track it stands on: the track pins its one pin is wired to.
  The model says which piece of track that is, by the piece's name: the circuit that a track circuit marker or a
  switch's TC names there; else the name of an end of track on it, an industry; else a name made from one of its pins.
  Track with no circuit is track like any other: an appliance stands on it without error.
  A piece nobody named is reported for information when an appliance stands on it.
  The circuit an appliance stands on is a circuit of its own interlocking.
  One that states no track is placed by its Milepost and CP Name.
  Lamp, contact and actuator are read the same way; no rule tells an actuator from a lamp yet.
  A contact states its own token, as a field lamp does: a sensor's source is the field contact named for it
  (the owner, 2026-11-05), so a desk lamp that consumes the token finds it reported by the contact.

  Scenario: a contact on the track of a track circuit
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance     |
      | 1NAT | track_circuit |
      | HTR  | contact       |
    And interlocking "Luchessa" has these wires:
      | Pins              |
      | 1NAT.TC HTR.track |
    When the layout is derived
    Then "HTR" stands on "Luchessa:1NAT"
    And "HTR" is on circuit "Luchessa:1NAT"

  Scenario: an actuator on a switch's OS circuit
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance | TC    |
      | 783  | switch    | 783T1 |
      | HTR  | actuator  |       |
    And interlocking "Luchessa" has these wires:
      | Pins            |
      | 783.N HTR.track |
    When the layout is derived
    Then "HTR" stands on "Luchessa:783T1"
    And "HTR" is on circuit "Luchessa:783T1"

  @appliance.track.unnamed
  Scenario: a lamp on track that an industry names
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance |
      | 1    | switch    |
      | NFL  | lamp      |
    And interlocking "Luchessa" has these ends:
      | Id | Kind     | Name       |
      | E1 | INDUSTRY | BeetLoader |
    And interlocking "Luchessa" has these wires:
      | Pins                       |
      | 1.R BeetLoader.EoT NFL.track |
    When the layout is derived
    Then "NFL" stands on "Luchessa:BeetLoader"
    And "NFL" is on no circuit
    And it is not reported

  @appliance.track.unnamed
  Scenario: a lamp on track nobody named
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance |
      | 1    | switch    |
      | NFL  | lamp      |
    And interlocking "Luchessa" has these wires:
      | Pins          |
      | 1.R NFL.track |
    When the layout is derived
    Then "NFL" stands on "track@Luchessa:1.R"
    And "NFL" is on no circuit
    And it is reported as information on "NFL"

  @appliance.circuit
  Scenario: a contact on track that another interlocking's circuit names
    Given interlocking "Luchessa" has these appliances:
      | Name | Appliance |
      | HTR  | contact   |
    And interlocking "Sargent" has these appliances:
      | Name | Appliance     |
      | 2NAT | track_circuit |
    And interlocking "Luchessa" has these wires:
      | Pins                      |
      | Sargent:2NAT.TC HTR.track |
    When the layout is derived
    Then it is reported as an error on "HTR"

  @reference.unresolved
  Scenario: a contact states its own token, which a desk lamp consumes
    Given interlocking "Sargent" has house "Sargent"
    And interlocking "Sargent" is on a code line
    And interlocking "Sargent" has these appliances:
      | Name | Appliance     | Indication |
      | 2NAT | track_circuit | 2NATK      |
      | HBA  | contact       | HBAK       |
    And interlocking "Sargent" has these wires:
      | Pins              |
      | 2NAT.TC HBA.track |
    And the desk has these lamps for interlocking "Sargent":
      | Name | Indication   |
      | HBD  | Sargent:HBAK |
    When the layout is derived
    Then "HBA" reports "HBAK" as a contact
    And it is not reported

  @appliance.circuit
  Scenario: a lamp that states no track
    Given interlocking "Luchessa" has house "Luchessa"
    And interlocking "Luchessa" has these appliances:
      | Name | Appliance | Milepost | CP Name  |
      | NFL  | lamp      | 78.1     | Luchessa |
    When the layout is derived
    Then it is not reported
