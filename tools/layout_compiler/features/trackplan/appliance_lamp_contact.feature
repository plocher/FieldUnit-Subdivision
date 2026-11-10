Feature: The pin of a lamp, contact or actuator
  A lamp, contact or actuator appliance has one pin: SENSOR, LAMP or ACTUATOR, a maintainer call's MC.
  Wired to a track net, the pin states the track the appliance stands on: every track pin on that net, as its
  track relation. Track with no circuit is track like any other.
  Wired to a house's MC pin, the appliance is that house's maintainer call: its house relation.
  Wired to any other net, it is an error.
  Not wired, the appliance is placed by its Milepost and CP Name.
  A switch heater is wired to its switch's N pin like track.
  Lamp, contact and actuator are read the same way; no rule tells an actuator from a lamp yet.

  Scenario: a contact wired to the track
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role      | Appliance     | Name |
      | TC1 | Railroad-Trackplan:Track Circuit | APPLIANCE | track_circuit | 1NAT |
      | K1  | Railroad-Trackplan:Sensor        | APPLIANCE | contact       | HTR  |
    And these nets:
      | Net | Pins              |
      | w   | TC1.TC K1.SENSOR  |
    When the drawing is imported
    Then "HTR" names "X:1NAT.TC" on side track

  Scenario: a switch heater wired to its switch's N pin
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role      | Appliance | Style   | Name | TC    |
      | SW1 | Railroad-Trackplan:Switch_Powered | APPLIANCE | switch    | powered | 783  | 783T1 |
      | K1  | Railroad-Trackplan:Sensor         | APPLIANCE | contact   |         | HTR  |       |
    And these nets:
      | Net | Pins             |
      | n   | SW1.N K1.SENSOR  |
    When the drawing is imported
    Then "HTR" names "X:783.N" on side track

  Scenario: an actuator wired to the track
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role      | Appliance     | Name |
      | TC1 | Railroad-Trackplan:Track Circuit | APPLIANCE | track_circuit | 1NAT |
      | A1  | Railroad-Trackplan:Actuator      | APPLIANCE | actuator      | HTR  |
    And these nets:
      | Net | Pins                |
      | w   | TC1.TC A1.ACTUATOR  |
    When the drawing is imported
    Then "HTR" names "X:1NAT.TC" on side track

  @appliance.track_pin
  Scenario: a lamp wired to track with no circuit
    Given this drawing of interlocking "X":
      | Ref | Symbol                  | Role      | Kind | Appliance | Name |
      | J1  | Railroad-Trackplan:IRJ  | TRACK     | IRJ  |           |      |
      | L1  | Railroad-Trackplan:Lamp | APPLIANCE |      | lamp      | NFL  |
    And these nets:
      | Net | Pins            |
      | w   | J1.A L1.LAMP    |
    When the drawing is imported
    Then "NFL" names "J1.A" on side track
    And it is not reported

  Scenario: a maintainer call wired to its house
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role      | Kind          | Appliance | Style           | Name | CP Name |
      | H1  | Railroad-Trackplan:House          | STRUCTURE | CONTROL_POINT |           |                 |      | East    |
      | MC1 | Railroad-Trackplan:MaintainerCall | APPLIANCE |               | lamp      | maintainer_call | 1MC  |         |
    And these nets:
      | Net | Pins           |
      | mc  | H1.MC MC1.MC   |
    When the drawing is imported
    Then "1MC" stands on no track
    And "1MC" states the relation house "X:East"

  @appliance.track_pin
  Scenario: a lamp wired to a net that is not track
    Given this drawing of interlocking "X":
      | Ref | Symbol                                | Role      | Kind       | Appliance | Name  |
      | J1  | Railroad-Trackplan:IRJ-Signal         | TRACK     | IRJ_SIGNAL |           |       |
      | M1  | Railroad-Trackplan:Signal Mast Single | APPLIANCE | CONTROLLED | mast      | 784EA |
      | L1  | Railroad-Trackplan:Lamp               | APPLIANCE |            | lamp      | NFL   |
    And these nets:
      | Net | Pins                          |
      | sig | J1.SIGNAL M1.SIGNAL L1.LAMP   |
    When the drawing is imported
    Then it is reported as an error on "L1"
    And "NFL" stands on no track

  @appliance.track_pin
  Scenario: a lamp with its pin not wired
    Given this drawing of interlocking "X":
      | Ref | Symbol                   | Role      | Kind          | Appliance | Name | CP Name | Milepost |
      | H1  | Railroad-Trackplan:House | STRUCTURE | CONTROL_POINT |           |      | East    |          |
      | L1  | Railroad-Trackplan:Lamp  | APPLIANCE |               | lamp      | NFL  | East    | 78.1     |
    When the drawing is imported
    Then it is not reported
    And "NFL" stands on no track
