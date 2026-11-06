Feature: The TRACK pin of a lamp or contact
  A lamp or contact appliance has one optional pin, TRACK.
  Wired to a track net, the pin states the track circuit the appliance is at.
  Wired to any other net, it is an error.
  Not wired, the appliance is placed by its Milepost and CP Name.
  A switch heater is wired to its switch's N pin like track.

  @pending
  Scenario: a contact wired to the track
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role      | Appliance     | Name |
      | TC1 | Railroad-Trackplan:Track Circuit | APPLIANCE | track_circuit | 1NAT |
      | K1  | Railroad-Trackplan:Contact       | APPLIANCE | contact       | HTR  |
    And these nets:
      | Net | Pins             |
      | w   | TC1.TC K1.TRACK  |
    When the drawing is imported
    Then "HTR" states the circuit "X:1NAT"

  @pending
  Scenario: a switch heater wired to its switch's N pin
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role      | Appliance     | Style   | Name | TC    |
      | SW1 | Railroad-Trackplan:Switch_Powered | APPLIANCE | switch        | powered | 783  | 783T1 |
      | K1  | Railroad-Trackplan:Contact        | APPLIANCE | contact       |         | HTR  |       |
    And these nets:
      | Net | Pins            |
      | n   | SW1.N K1.TRACK  |
    When the drawing is imported
    Then "HTR" states the circuit "X:783T1"

  @pending @appliance.track_pin
  Scenario: a lamp wired to a net that is not track
    Given this drawing of interlocking "X":
      | Ref  | Symbol                           | Role      | Kind          | Appliance | Name | CP Name |
      | H1   | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |           |      | East    |
      | AUX1 | Railroad-Trackplan:AUXILIARY     | APPLIANCE |               | lamp      | NFL  |         |
    And these nets:
      | Net | Pins              |
      | mc  | H1.MC AUX1.TRACK  |
    When the drawing is imported
    Then it is reported as an error on "AUX1"

  @pending @appliance.track_pin
  Scenario: a lamp with its TRACK pin not wired
    Given this drawing of interlocking "X":
      | Ref  | Symbol                       | Role      | Kind          | Appliance | Name | CP Name | Milepost |
      | H1   | Railroad-Trackplan:House     | STRUCTURE | CONTROL_POINT |           |      | East    |          |
      | AUX1 | Railroad-Trackplan:AUXILIARY | APPLIANCE |               | lamp      | NFL  | East    | 78.1     |
    When the drawing is imported
    Then it is not reported
    And "NFL" states no circuit
