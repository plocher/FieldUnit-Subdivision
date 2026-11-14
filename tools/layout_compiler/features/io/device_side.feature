Feature: A device is on the side of the processor its bindings reach
  A device symbol states what it is, never where it is used (ADR 0017).
  A device bound to the desk's processor is a desk device, wherever it is drawn. A device bound to a field unit's processor is that interlocking's.
  A device with no binding is a desk device when its Column pin is wired to a column. Otherwise it is the device of the interlocking whose sheet it is drawn on.
  A column comes from a wired Column pin, never from Role. A Column pin on a device bound to a field unit is an error.
  Bindings that reach the desk and a field unit are an error. A field device drawn under another interlocking's sheet is a warning.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                 | Role      | Appliance | Style  | IC      | Address | Name    |
      | SW  | Railroad-Trackplan:Switch_Powered      | APPLIANCE | switch    | powered |        |         | 3       |
      | X1  | Railroad-HardwareIO:Driver-I2C-MAX7311 | IODRIVER  |           |        | MAX7311 | 0x20    |         |
    And these symbols on the sheet above:
      | Ref | Symbol                                 | Role        | Kind      | IC      | Address | Name | Board | Column |
      | OU  | Railroad-Office:OfficeUnit             | OFFICE_UNIT |           |         |         | Desk |       |        |
      | PD  | Railroad-HardwareIO:Processor          | STRUCTURE   | PROCESSOR |         |         | Dsk  | Mega  |        |
      | XD  | Railroad-HardwareIO:Driver-I2C-MAX7311 | IODRIVER    |           | MAX7311 | 0x50    |      |       |        |
      | C1  | Railroad-Office:PanelColumn            | COLUMN      |           |         |         |      |       | 1      |
    And these nets:
      | Net  | Pins                |
      | desk | OU.Processor PD.Processor |
      | dbus | PD.IOBus XD.IOBus   |
      | bus  | P1.IOBus X1.IOBus   |

  Scenario: a desk selector drawn on an interlocking's sheet
    Given these symbols too:
      | Ref | Symbol                       | Role   | Appliance | Name    |
      | SEL | Railroad-Office:PanelSelector | DEVICE | selector  | Arrival |
    And these nets:
      | Net | Pins          |
      | v   | SEL.VALUE XD.P0 |
    When the drawing is imported
    Then the device "SEL" is a device of office unit "Desk"
    And the device "SEL" is in no column

  Scenario: a switch machine bound to its interlocking's processor
    Given these symbols too:
      | Ref | Symbol                       | Role   | Appliance | Name |
      | DS  | Railroad-Field:Device-Switch | DEVICE | switch    | 3    |
    And these nets:
      | Net | Pins         |
      | m   | DS.M X1.P0   |
    When the drawing is imported
    Then the device "DS" is a device of interlocking "X"

  Scenario: a desk lever in its column
    Given these symbols too:
      | Ref | Symbol                      | Role  | Appliance | Style  | Name |
      | LV  | Railroad-Office:PanelSwitch | PANEL | lever     | switch | 3    |
    And these nets:
      | Net | Pins            |
      | col | LV.Column C1.P1 |
      | nws | LV.NWS XD.P1    |
    When the drawing is imported
    Then the device "LV" is a device of office unit "Desk"
    And the device "LV" is in column "Desk:1"

  Scenario: a device with no binding in a column is the desk's
    Given these symbols too:
      | Ref | Symbol                      | Role  | Appliance | Style  | Name |
      | LV  | Railroad-Office:PanelSwitch | PANEL | lever     | switch | 3    |
    And these nets:
      | Net | Pins            |
      | col | LV.Column C1.P1 |
    When the drawing is imported
    Then the device "LV" is a device of office unit "Desk"
    And the device "LV" is in column "Desk:1"

  Scenario: a device with no binding and no column is its sheet's
    Given these symbols too:
      | Ref | Symbol                       | Role   | Appliance | Name |
      | DS  | Railroad-Field:Device-Switch | DEVICE | switch    | 3    |
    When the drawing is imported
    Then the device "DS" is a device of interlocking "X"

  @device.sides
  Scenario: a device bound to the desk and to a field unit
    Given these symbols too:
      | Ref | Symbol                      | Role   | Appliance | Style  | Name |
      | LF  | Railroad-Field:Local-Switch | DEVICE | lever     | switch | 3    |
    And these nets:
      | Net | Pins          |
      | nws | LF.NWS XD.P0  |
      | rws | LF.RWS X1.P0  |
    When the drawing is imported
    Then it is reported as an error on "LF"

  @device.side.sheet
  Scenario: a field device drawn under another interlocking's sheet
    Given this drawing of interlocking "Y":
      | Ref | Symbol                                 | Role     | IC      | Address |
      | Y1  | Railroad-HardwareIO:Driver-I2C-MAX7311 | IODRIVER | MAX7311 | 0x20    |
    And these symbols too:
      | Ref | Symbol                       | Role   | Appliance | Name |
      | DS  | Railroad-Field:Device-Switch | DEVICE | switch    | 3    |
    And these nets:
      | Net  | Pins              |
      | ybus | P2.IOBus Y1.IOBus |
      | m    | DS.M Y1.P0        |
    When the drawing is imported
    Then the device "DS" is a device of interlocking "Y"
    And it is reported as a warning on "DS"

  @device.column.field
  Scenario: a field device wired to a desk column
    Given these symbols too:
      | Ref | Symbol                      | Role  | Appliance | Style  | Name |
      | LV  | Railroad-Office:PanelSwitch | PANEL | lever     | switch | 3    |
    And these nets:
      | Net | Pins            |
      | col | LV.Column C1.P1 |
      | nws | LV.NWS X1.P1    |
    When the drawing is imported
    Then it is reported as an error on "LV"

  Scenario: one processor runs two interlockings, and the appliance the device serves says which
    Given interlocking "Y" shares the processor of "X", in this drawing:
      | Ref | Symbol                            | Role      | Appliance | Style   | Name |
      | SY  | Railroad-Trackplan:Switch_Powered | APPLIANCE | switch    | powered | 9    |
    And these symbols too:
      | Ref | Symbol                       | Role   | Appliance | Name |
      | DS  | Railroad-Field:Device-Switch | DEVICE | switch    | 9    |
    And these nets:
      | Net | Pins       |
      | m   | DS.M X1.P0 |
    When the drawing is imported
    Then the device "DS" is a device of interlocking "Y"
