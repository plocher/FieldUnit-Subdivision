Feature: A derail, as drawn
  The derail symbols (Derail, Derail Dual, Derail Local, Derail Manual Sensed, Derail Manual) are Appliance switch
  with the word derail in their Style and the switch word of their regime, pins C and R. The importer reads the
  word derail, never the whole Style, to know the ports. A derail has no TC pin and no TC field: it lies on the
  net its ports are on. A lever named for it (Local-Derail, PanelSwitch) serves it as any lever serves a switch.
  (The owner, 2026-11-09)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                             | Role      | Kind          | Appliance     | Style          | Name  | CP Name | TC    |
      | H1  | Railroad-Trackplan:House           | STRUCTURE | CONTROL_POINT |               |                |       | East    |       |
      | TC1 | Railroad-Trackplan:Track Circuit   | APPLIANCE |               | track_circuit |                | 1T    |         |       |
      | SW1 | Railroad-Trackplan:Switch_Lock     | APPLIANCE |               | switch        | lock           | 795   |         | 795T1 |
      | D1  | Railroad-Trackplan:Derail          | APPLIANCE |               | switch        | derail,powered | 795D  |         |       |
      | D2  | Railroad-Trackplan:Derail Manual   | APPLIANCE |               | switch        | derail,manual  | 5     |         |       |

  Scenario: a derail's ports are C and R, read from the word derail
    Given these nets:
      | Net | Pins          |
      | a   | SW1.N TC1.TC  |
      | b   | SW1.R D1.R    |
      | c   | D1.C D2.C     |
    When the drawing is imported
    Then "795D" names "X:795.R" on side R
    And "795D" names "X:5.C" on side C
    And "5" names "X:795D.C" on side C
