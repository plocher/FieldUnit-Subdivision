Feature: A virtual track circuit, as drawn
  Track Circuit_Virtual is Appliance track_circuit, Style virtual, with a Members field and no
  track pin: it stands on no track and its Members are written as given. (ADR 0013 §7.2)

  Scenario: a virtual circuit states its members and stands on no track
    Given this drawing of interlocking "X":
      | Ref | Symbol                                   | Role      | Kind          | Appliance     | Style   | Name | Members   | CP Name |
      | H1  | Railroad-Trackplan:House                 | STRUCTURE | CONTROL_POINT |               |         |      |           | East    |
      | TC1 | Railroad-Trackplan:Track Circuit         | APPLIANCE |               | track_circuit |         | 832T |           |         |
      | TC2 | Railroad-Trackplan:Track Circuit         | APPLIANCE |               | track_circuit |         | 834T |           |         |
      | V1  | Railroad-Trackplan:Track Circuit_Virtual | APPLIANCE |               | track_circuit | virtual | 831T | 832T,834T |         |
    And these nets:
      | Net | Pins   |
      | a   | TC1.TC |
      | b   | TC2.TC |
    When the drawing is imported
    Then "831T" is written with Members "832T,834T"
    And "831T" stands on no track
