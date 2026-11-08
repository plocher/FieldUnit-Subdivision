Feature: A train order board stands at a station
  A train order board is used in Time Table and Train Order territory, never in CTC.
  It names the timetable station it stands at.
  It is in no control point.
  It has no head of its own: its faces are the units of its field device.

  @train_order.station
  Scenario: a board that names no station
    Given interlocking "Gilroy" has these appliances:
      | Name   | Appliance   |
      | Gilroy | train_order |
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.station
  Scenario: a board at a station the timetable does not have
    Given interlocking "Gilroy" has these appliances:
      | Name   | Appliance   | Station | relations.station |
      | Gilroy | train_order | Gilroy  | Gilroy            |
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.station
  Scenario: a board at a station of the timetable
    Given the timetable has station "Gilroy"
    And interlocking "Gilroy" has these appliances:
      | Name   | Appliance   | Station | relations.station |
      | Gilroy | train_order | Gilroy  | Gilroy            |
    When the layout is derived
    Then it is not reported

  Scenario: a board is in no control point
    Given the timetable has station "Gilroy"
    And interlocking "Gilroy" has house "Gilroy"
    And interlocking "Gilroy" has these appliances:
      | Name   | Appliance   | Station | relations.station |
      | Gilroy | train_order | Gilroy  | Gilroy            |
    When the layout is derived
    Then "Gilroy" has no derived controlPoint
